import requests

import crs as crs_def
from geoserver.util import wfs_direct, wms_direct
from layman import app, settings
from layman.layer.geoserver import wfs
from .util import url_for


def get_url(workspace, service_endpoint):
    subpath = workspace + '/' + service_endpoint if workspace else service_endpoint
    with app.app_context():
        wfs_url = url_for('geoserver_proxy_bp.proxy', subpath=subpath)
    return wfs_url


def get_wms_url(workspace, service_endpoint='ows'):
    return get_url(workspace, service_endpoint)


def get_wfs_url(workspace, service_endpoint='wfs'):
    return get_url(workspace, service_endpoint)


def get_wfs_capabilities(workspace=None, service_endpoint='wfs', headers=None, version=None):
    wfs_url = get_url(workspace, service_endpoint)
    return wfs_direct(wfs_url, headers=headers, version=version)


def get_wms_capabilities(workspace=None, service_endpoint='ows', headers=None, version=None):
    wms_url = get_url(workspace, service_endpoint)
    return wms_direct(wms_url, headers=headers, version=version)


def get_crs_urn(crs):
    urn = crs_def.CRS_URN.get(crs)
    if not urn:
        crs_authority, crs_code = crs.split(':')
        urn = f"urn:ogc:def:crs:{crs_authority}::{crs_code}"
    return urn


def get_features(workspace, feature_type, crs=crs_def.EPSG_3857):
    wfs_url = get_wfs_url(workspace)
    crs_urn = get_crs_urn(crs)
    response = requests.get(wfs_url, params={
        'service': 'WFS',
        'request': 'GetFeature',
        'version': wfs.VERSION,
        'typeNames': f"{workspace}:{feature_type}",
        'outputFormat': f"application/json",
        'srsName': crs_urn,
    }, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    response.raise_for_status()
    result = response.json()

    def get_equivalent_crs_urns(crs):
        urns = {get_crs_urn(crs)}
        if crs in [crs_def.EPSG_4326, crs_def.CRS_84]:
            urns.update([
                'urn:ogc:def:crs:EPSG::4326',
                'urn:ogc:def:crs:CRS::84',
                'urn:ogc:def:crs:OGC:1.3:CRS84',
            ])
        return urns
    actual_urn = result['crs']['properties']['name']
    accepted_urns = get_equivalent_crs_urns(crs)
    assert actual_urn in accepted_urns, \
        f"Unexpected CRS URN: {actual_urn}, expected one of: {accepted_urns}"
    return result
