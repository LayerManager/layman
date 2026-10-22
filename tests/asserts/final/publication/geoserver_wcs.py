import uuid

import requests
from lxml import etree as ET
from osgeo import gdal

from layman import app, settings, util as layman_util
from layman.layer.geoserver import GeoserverIds, wcs as gs_wcs
from layman.layer.layer_class import Layer
from test_tools import process_client, util as test_util

WCS_ACCESS_DENIED_EXCEPTION_CODES = frozenset({
    'LayerNotDefined',
    'CoverageNotDefined',
    'AccessDenied',
    'Forbidden',
})


def _local_name(tag):
    return tag.split('}', 1)[-1] if isinstance(tag, str) else tag


def _wcs_1_0_0_coverage_names(caps_content):
    """Coverage names from WCS 1.0.0 GetCapabilities (CoverageOfferingBrief/name)."""
    root = ET.fromstring(caps_content)
    names = set()
    for brief in root.iter():
        if _local_name(brief.tag) not in ('CoverageOfferingBrief', 'ContentOfferingBrief'):
            continue
        names.update(
            child.text.strip()
            for child in brief
            if _local_name(child.tag) == 'name' and child.text
        )
    return names


def _coverage_name_matches(advertised_name, coverage_name):
    return coverage_name in (
        advertised_name,
        advertised_name.rsplit(':', maxsplit=1)[-1],
    )


def _assert_wcs_caps_contains_coverage(response, coverage_name):
    assert response.status_code == 200, response.text
    names = _wcs_1_0_0_coverage_names(response.content)
    assert any(_coverage_name_matches(name, coverage_name) for name in names), (
        f"Coverage {coverage_name} not found among WCS GetCapabilities offerings {sorted(names)}.\n"
        f"{response.text[:2000]}"
    )


def _assert_wcs_caps_lacks_coverage(response, coverage_name):
    assert response.status_code == 200, response.text
    names = _wcs_1_0_0_coverage_names(response.content)
    assert not any(_coverage_name_matches(name, coverage_name) for name in names), (
        f"Coverage {coverage_name} still present in WCS GetCapabilities offerings.\n"
        f"{response.text[:2000]}"
    )


def _geotiff_summary(content, *, context):
    path = f'/vsimem/layman_wcs_assert_{uuid.uuid4().hex}.tif'
    gdal.FileFromMemBuffer(path, content)
    dataset = None
    try:
        dataset = gdal.Open(path)
        assert dataset is not None, f'{context}: GDAL failed to open GetCoverage response as GeoTIFF'
        assert dataset.RasterCount > 0, f'{context}: GeoTIFF has no raster bands'
        checksums = tuple(
            dataset.GetRasterBand(index).Checksum()
            for index in range(1, dataset.RasterCount + 1)
        )
        return (dataset.RasterXSize, dataset.RasterYSize, dataset.RasterCount), checksums
    finally:
        dataset = None
        gdal.Unlink(path)


def _assert_response_is_geotiff(response, *, context):
    assert response.status_code == 200, f'{context}: status={response.status_code}\n{response.text[:2000]}'
    content_type = response.headers.get('Content-Type', '').lower()
    assert 'xml' not in content_type, f'{context}: XML instead of GeoTIFF\n{response.text[:2000]}'
    return _geotiff_summary(response.content, context=context)


def _assert_wcs_access_denied(response, *, coverage_name):
    if response.status_code in (401, 403):
        return
    assert response.status_code in (200, 400), (
        f'Expected 401/403 or WCS ServiceException for coverage {coverage_name}, '
        f'got status={response.status_code}\n{response.text[:2000]}'
    )
    try:
        root = ET.fromstring(response.content)
    except ET.XMLSyntaxError as exc:
        raise AssertionError(
            f'Expected 401/403 or WCS ServiceExceptionReport for coverage {coverage_name}, '
            f'got status={response.status_code} content-type='
            f'{response.headers.get("Content-Type", "")!r}\n{response.content[:500]!r}'
        ) from exc

    exceptions = [
        (
            element.get('code') or element.get('exceptionCode'),
            element.get('locator'),
            (element.text or '').strip(),
        )
        for element in root.iter()
        if _local_name(element.tag) in ('ServiceException', 'Exception')
    ]
    assert exceptions, (
        f'No ServiceException/Exception in response for coverage {coverage_name}\n'
        f'{response.text[:2000]}'
    )

    def is_access_denied(code, locator, text):
        if code in WCS_ACCESS_DENIED_EXCEPTION_CODES:
            return True
        if code == 'InvalidParameterValue' and locator and locator.lower() in {
            'coverage', 'coverageid', 'identifier',
        }:
            text_lower = text.lower()
            return (
                coverage_name in text
                or 'could not find coverage' in text_lower
                or 'coverage not found' in text_lower
                or 'unknown coverage' in text_lower
            )
        return False

    assert any(is_access_denied(code, locator, text) for code, locator, text in exceptions), (
        f'Expected access-denied ServiceException for coverage {coverage_name}, '
        f'got {exceptions}\nstatus={response.status_code}\n{response.text[:2000]}'
    )


def _get_wcs_url(gs_layername):
    with app.app_context():
        return test_util.url_for('geoserver_proxy_bp.proxy', subpath=gs_layername.workspace + '/wcs')


def _get_coverage_params(gs_layername, file_info):
    minx, miny, maxx, maxy = file_info['native_bounding_box']
    width, height = (10, 10) if minx != maxx and miny != maxy else (1, 1)
    return {
        'SERVICE': 'WCS',
        'REQUEST': 'GetCoverage',
        'VERSION': gs_wcs.VERSION,
        'COVERAGE': gs_layername.name,
        'CRS': file_info['native_crs'],
        'BBOX': f'{minx},{miny},{maxx},{maxy}',
        'WIDTH': width,
        'HEIGHT': height,
        'FORMAT': 'geotiff',
    }


def _get_file_info(workspace, publ_type, name, keys):
    with app.app_context():
        publ_uuid = layman_util.get_publication_uuid(workspace, publ_type, name)
        info = layman_util.get_publication_info(Layer(uuid=publ_uuid, load=False), {'keys': keys})
    return publ_uuid, info


def workspace_wcs_1_0_0_available_if_raster(workspace, publ_type, name, headers=None, *, actor_name=None):
    headers = headers or {}
    if actor_name:
        assert process_client.TOKEN_HEADER not in headers
    if actor_name and actor_name != settings.ANONYM_USER:
        headers.update(process_client.get_authz_headers(actor_name))

    publ_uuid, file_info = _get_file_info(
        workspace,
        publ_type,
        name,
        ['geodata_type', 'native_bounding_box', 'native_crs'],
    )
    if file_info['geodata_type'] != settings.GEODATA_TYPE_RASTER:
        return

    gs_layername = GeoserverIds(uuid=publ_uuid).wms
    wcs_url = _get_wcs_url(gs_layername)
    caps_response = requests.get(
        wcs_url,
        params={'SERVICE': 'WCS', 'REQUEST': 'GetCapabilities', 'VERSION': gs_wcs.VERSION},
        headers=headers,
        timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
    )
    _assert_wcs_caps_contains_coverage(caps_response, gs_layername.name)
    coverage_response = requests.get(
        wcs_url,
        params=_get_coverage_params(gs_layername, file_info),
        headers=headers,
        timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
    )
    _assert_response_is_geotiff(coverage_response, context=f'WCS GetCoverage {gs_layername.name}')


def workspace_wcs_1_0_0_timeseries_matches_wms_time(workspace, publ_type, name, headers=None, *, actor_name=None):
    headers = headers or {}
    if actor_name and actor_name != settings.ANONYM_USER:
        headers.update(process_client.get_authz_headers(actor_name))

    publ_uuid, info = _get_file_info(
        workspace,
        publ_type,
        name,
        ['geodata_type', 'wms', 'native_bounding_box', 'native_crs'],
    )
    if info['geodata_type'] != settings.GEODATA_TYPE_RASTER:
        return
    wms_time = info.get('wms', {}).get('time')
    if not wms_time:
        return

    time_values = wms_time['values']
    default_time = wms_time['default']
    assert default_time in time_values, f"wms.time.default {default_time} not in values {time_values}"
    assert len(time_values) >= 2, f"Need at least two time granules to compare TIME selection, got {time_values}"
    other_time = next(value for value in time_values if value != default_time)

    gs_layername = GeoserverIds(uuid=publ_uuid).wms
    wcs_url = _get_wcs_url(gs_layername)
    caps_response = requests.get(
        wcs_url,
        params={'SERVICE': 'WCS', 'REQUEST': 'GetCapabilities', 'VERSION': gs_wcs.VERSION},
        headers=headers,
        timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
    )
    _assert_wcs_caps_contains_coverage(caps_response, gs_layername.name)

    describe_response = requests.get(
        wcs_url,
        params={
            'SERVICE': 'WCS',
            'REQUEST': 'DescribeCoverage',
            'VERSION': gs_wcs.VERSION,
            'COVERAGE': gs_layername.name,
        },
        headers=headers,
        timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
    )
    assert describe_response.status_code == 200, describe_response.text
    describe_root = ET.fromstring(describe_response.content)
    time_positions = {
        (element.text or '').strip()
        for element in describe_root.iter()
        if _local_name(element.tag) == 'timePosition' and element.text
    }
    for time_value in time_values:
        assert time_value in time_positions or any(
            position.startswith(time_value[:10]) for position in time_positions
        ), f"DescribeCoverage missing time value {time_value}; timePositions={sorted(time_positions)}"

    coverage_params = _get_coverage_params(gs_layername, info)

    def fetch_coverage(*, time_value=None, label):
        params = dict(coverage_params)
        if time_value is not None:
            params['TIME'] = time_value
        response = requests.get(
            wcs_url,
            params=params,
            headers=headers,
            timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
        )
        return _assert_response_is_geotiff(response, context=label)

    without_time = fetch_coverage(label=f'WCS GetCoverage {gs_layername.name} without TIME')
    with_default = fetch_coverage(
        time_value=default_time,
        label=f'WCS GetCoverage {gs_layername.name} TIME={default_time} (default/MAXIMUM)',
    )
    with_other = fetch_coverage(time_value=other_time, label=f'WCS GetCoverage {gs_layername.name} TIME={other_time}')

    assert without_time == with_default, (
        f'GetCoverage without TIME must match TIME={default_time} (wms.time.default / MAXIMUM); '
        f'without_time={without_time}, with_default={with_default}'
    )
    assert with_other != with_default, (
        f'TIME={other_time} must select a different granule than default TIME={default_time}; '
        f'both produced {with_default}'
    )


def workspace_wcs_1_0_0_coverage_absent(workspace, publ_type, name, headers=None, *, actor_name=None):
    headers = headers or {}
    if actor_name and actor_name != settings.ANONYM_USER:
        headers.update(process_client.get_authz_headers(actor_name))
    with app.app_context():
        publ_uuid = layman_util.get_publication_uuid(workspace, publ_type, name)
    gs_layername = GeoserverIds(uuid=publ_uuid).wms
    caps_response = requests.get(
        _get_wcs_url(gs_layername),
        params={'SERVICE': 'WCS', 'REQUEST': 'GetCapabilities', 'VERSION': gs_wcs.VERSION},
        headers=headers,
        timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
    )
    _assert_wcs_caps_lacks_coverage(caps_response, gs_layername.name)


def workspace_wcs_1_0_0_forbidden_without_read(workspace, publ_type, name, headers=None, *, actor_name=None):
    headers = headers or {}
    if actor_name and actor_name != settings.ANONYM_USER:
        headers.update(process_client.get_authz_headers(actor_name))
    publ_uuid, file_info = _get_file_info(
        workspace,
        publ_type,
        name,
        ['geodata_type', 'native_bounding_box', 'native_crs'],
    )
    if file_info['geodata_type'] != settings.GEODATA_TYPE_RASTER:
        return
    gs_layername = GeoserverIds(uuid=publ_uuid).wms
    coverage_response = requests.get(
        _get_wcs_url(gs_layername),
        params=_get_coverage_params(gs_layername, file_info),
        headers=headers,
        timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
    )
    _assert_wcs_access_denied(coverage_response, coverage_name=gs_layername.name)
