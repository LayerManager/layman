import json
from urllib.parse import urljoin

import pytest
import requests
from lxml import etree as ET
from micka import NAMESPACES

from geoserver import GS_REST_WORKSPACES
from layman import app, settings, common
from layman.layer.geoserver import GeoserverIds
from layman.layer.geoserver import wms
from layman.common.micka import util as common_util, requests as micka_requests
from layman.map.map_class import Map
from layman.layer.layer_class import Layer
from layman.map.micka import csw as map_csw
from layman.layer.micka import csw as layer_csw
from layman import upgrade
from layman.upgrade import upgrade_v3_0
from test_tools import process_client
from test_tools import util as test_util


def update_metadata_values(publication, *, metadata_properties_to_refresh=None, actor_name=None,
                           timeout=None, **kwargs):
    timeout = timeout or settings.DEFAULT_CONNECTION_TIMEOUT
    metadata_properties_to_refresh = metadata_properties_to_refresh or []
    assert len(metadata_properties_to_refresh) > 0, "metadata_properties_to_refresh cannot be empty"

    csw = common_util.create_csw()
    assert publication.uuid is not None, "publication.uuid cannot be None"
    assert csw is not None, "csw cannot be None"

    muuid = publication.micka_ids.id
    element = common_util.get_record_element_by_id(csw, muuid)
    assert element is not None, f"metadata record with muuid {muuid} does not exist"

    if isinstance(publication, Map):
        csw_module = map_csw
        csw_kwargs = {'http_method': common.REQUEST_METHOD_PATCH, 'actor_name': actor_name}
    elif isinstance(publication, Layer):
        csw_module = layer_csw
        csw_kwargs = {'http_method': common.REQUEST_METHOD_PATCH}
    else:
        raise ValueError(f"Unsupported publication type: {type(publication)}")

    _, prop_values = csw_module.get_template_path_and_values(publication, **csw_kwargs)
    prop_values.update(kwargs)
    prop_values = {
        k: v for k, v in prop_values.items()
        if k in metadata_properties_to_refresh + ['md_date_stamp']
    }
    element = common_util.fill_xml_template_obj(element, prop_values, csw_module.METADATA_PROPERTIES)
    record = ET.tostring(element, encoding='unicode', pretty_print=True)

    micka_requests.csw_update({
        'muuid': muuid,
        'record': record,
    }, timeout=timeout)


def get_metadata_property_elements(publication, property_name):
    csw = common_util.create_csw()
    element = common_util.get_record_element_by_id(csw, publication.micka_ids.id)
    assert element is not None
    metadata_property = layer_csw.METADATA_PROPERTIES[property_name]
    xpath_parent = metadata_property['xpath_parent'].split('/')[2:]
    xpath_parent.insert(0, '.')
    parent_elements = element.xpath('/'.join(xpath_parent), namespaces=NAMESPACES)
    assert len(parent_elements) == 1
    property_elements = parent_elements[0].xpath(
        metadata_property['xpath_property'],
        namespaces=NAMESPACES,
    )
    return element, property_elements


def remove_metadata_property(publication, property_name):
    element, property_elements = get_metadata_property_elements(publication, property_name)
    for property_element in property_elements:
        property_element.getparent().remove(property_element)
    micka_requests.csw_update({
        'muuid': publication.micka_ids.id,
        'record': ET.tostring(element, encoding='unicode', pretty_print=True),
    })


def test_wcs_url_metadata_migration_follows_existing_layer_metadata_migration():
    data_migrations = upgrade.MIGRATIONS[upgrade.consts.MIGRATION_TYPE_DATA]
    migration_list = next(migrations for version, migrations in data_migrations if version == (3, 0, 0))
    assert (
        migration_list.index(upgrade_v3_0.migrate_layer_wcs_url_metadata)
        > migration_list.index(upgrade_v3_0.migrate_layer_metadata_urls)
    )


@pytest.mark.usefixtures('ensure_layman')
def test_ensure_raster_coverage_wcs_configuration():
    workspace = 'test_wcs_formats_upgrade_workspace'
    name = 'test_wcs_formats_upgrade_layer'
    extra_crs = 'EPSG:3006'
    assert extra_crs not in settings.LAYMAN_OUTPUT_SRS_LIST
    published = process_client.publish_workspace_layer(
        workspace,
        name,
        file_paths=['sample/layman.layer/sample_tif_rgb.tif'],
    )
    publ_uuid = published['uuid']
    gs_layername = GeoserverIds(uuid=publ_uuid).wms
    coverage_store = wms.get_geotiff_store_name(uuid=publ_uuid)
    coverage_url = urljoin(
        GS_REST_WORKSPACES,
        f'{gs_layername.workspace}/coveragestores/{coverage_store}/coverages/{gs_layername.name}',
    )

    try:
        response = requests.put(
            coverage_url,
            data=json.dumps({
                'coverage': {
                    'supportedFormats': {
                        'string': ['ArcGrid', 'GEOTIFF'],
                    },
                    'requestSRS': {
                        'string': [extra_crs],
                    },
                    'responseSRS': {
                        'string': [extra_crs],
                    },
                },
            }),
            headers=upgrade_v3_0.gs_util.headers_json,
            auth=settings.LAYMAN_GS_AUTH,
            timeout=upgrade_v3_0.gs_util.GS_REST_TIMEOUT,
        )
        response.raise_for_status()

        upgrade_v3_0.ensure_raster_coverage_wcs_configuration()

        response = requests.get(
            coverage_url + '.json',
            headers=upgrade_v3_0.gs_util.headers_json,
            auth=settings.LAYMAN_GS_AUTH,
            timeout=upgrade_v3_0.gs_util.GS_REST_TIMEOUT,
        )
        response.raise_for_status()
        coverage = response.json()['coverage']
        formats = coverage['supportedFormats']['string']
        assert formats[0] == 'ArcGrid'
        assert set(upgrade_v3_0.gs_util.COVERAGE_SUPPORTED_FORMATS).issubset(formats)
        assert coverage['requestSRS']['string'][0] == extra_crs
        assert coverage['responseSRS']['string'][0] == extra_crs
        assert coverage['requestSRS']['string'] == coverage['responseSRS']['string']
        assert coverage['srs'] in coverage['requestSRS']['string']
        assert set(settings.LAYMAN_OUTPUT_SRS_LIST).issubset(coverage['requestSRS']['string'])
        first_wcs_configuration = {
            'formats': formats,
            'request_srs': coverage['requestSRS']['string'],
            'response_srs': coverage['responseSRS']['string'],
        }
        for values in first_wcs_configuration.values():
            assert len(values) == len(set(values))

        upgrade_v3_0.ensure_raster_coverage_wcs_configuration()

        response = requests.get(
            coverage_url + '.json',
            headers=upgrade_v3_0.gs_util.headers_json,
            auth=settings.LAYMAN_GS_AUTH,
            timeout=upgrade_v3_0.gs_util.GS_REST_TIMEOUT,
        )
        response.raise_for_status()
        coverage = response.json()['coverage']
        second_wcs_configuration = {
            'formats': coverage['supportedFormats']['string'],
            'request_srs': coverage['requestSRS']['string'],
            'response_srs': coverage['responseSRS']['string'],
        }
        assert second_wcs_configuration == first_wcs_configuration
    finally:
        process_client.delete_layer(publ_uuid, skip_404=True)


@pytest.mark.usefixtures('ensure_layman')
def test_migrate_layer_wcs_url_metadata():
    workspace = 'test_wcs_url_metadata_upgrade_workspace'
    raster_name = 'test_wcs_url_metadata_raster'
    vector_name = 'test_wcs_url_metadata_vector'
    raster_uuid = process_client.publish_workspace_layer(
        workspace,
        raster_name,
        file_paths=['sample/layman.layer/sample_tif_rgb.tif'],
    )['uuid']
    vector_uuid = process_client.publish_workspace_layer(
        workspace,
        vector_name,
        file_paths=['sample/layman.layer/small_layer.geojson'],
    )['uuid']

    try:
        with app.app_context():
            raster = Layer(uuid=raster_uuid)
            vector = Layer(uuid=vector_uuid)
            _, raster_values = layer_csw.get_template_path_and_values(
                raster,
                http_method=common.REQUEST_METHOD_PATCH,
            )
        expected_wcs_url = raster_values['wcs_url']
        remove_metadata_property(raster, 'wcs_url')

        raster_metadata = next(iter(layer_csw.get_metadata_comparison(raster).values()))
        assert raster_metadata['wcs_url'] is None
        _, wcs_elements = get_metadata_property_elements(raster, 'wcs_url')
        assert wcs_elements == []

        upgrade_v3_0.migrate_layer_wcs_url_metadata()

        raster_metadata = next(iter(layer_csw.get_metadata_comparison(raster).values()))
        assert raster_metadata['wcs_url'] == expected_wcs_url
        _, wcs_elements = get_metadata_property_elements(raster, 'wcs_url')
        assert len(wcs_elements) == 1
        first_wcs_url = raster_metadata['wcs_url']

        upgrade_v3_0.migrate_layer_wcs_url_metadata()

        raster_metadata = next(iter(layer_csw.get_metadata_comparison(raster).values()))
        assert raster_metadata['wcs_url'] == first_wcs_url
        _, wcs_elements = get_metadata_property_elements(raster, 'wcs_url')
        assert len(wcs_elements) == 1

        vector_metadata = next(iter(layer_csw.get_metadata_comparison(vector).values()))
        assert vector_metadata['wcs_url'] is None
        _, wcs_elements = get_metadata_property_elements(vector, 'wcs_url')
        assert wcs_elements == []
    finally:
        process_client.delete_layer(raster_uuid, skip_404=True)
        process_client.delete_layer(vector_uuid, skip_404=True)


@pytest.mark.parametrize('class_type,process_func,url_endpoint,test_uuid,publ_type,csw_module,migrate_func,delete_func', [
    (Map, process_client.publish_workspace_map, 'rest_map_thumbnail.get', 'af238200-8200-1a23-9399-42c9fca53543', 'map', map_csw, upgrade_v3_0.migrate_map_metadata_urls, process_client.delete_map),
    (Layer, process_client.publish_workspace_layer, 'rest_layer_thumbnail.get', 'bf238200-8200-1a23-9399-42c9fca53544', 'layer', layer_csw, upgrade_v3_0.migrate_layer_metadata_urls, process_client.delete_layer),
])
@pytest.mark.usefixtures('ensure_layman')
def test_update_graphic_url_metadata(class_type, process_func, url_endpoint, test_uuid, publ_type, csw_module, migrate_func, delete_func):
    workspace = 'test_workspace'
    publ_name = f'test_{publ_type}'

    with app.app_context():
        process_client.ensure_workspace(workspace)
        process_func(
            workspace=workspace,
            name=publ_name,
            uuid=test_uuid
        )

    old_thumbnail_url = f"{settings.LAYMAN_SERVER_NAME}/rest/workspaces/{workspace}/{publ_type}s/{publ_name}/thumbnail"
    old_file_url = f"{settings.LAYMAN_SERVER_NAME}/rest/workspaces/{workspace}/{publ_type}s/{publ_name}/file" if publ_type == 'map' else None

    with app.app_context():
        publication = class_type(uuid=test_uuid)
        metadata_properties_to_refresh = ['graphic_url']
        kwargs = {'graphic_url': old_thumbnail_url}

        if publ_type == 'map':
            metadata_properties_to_refresh.append('map_file_endpoint')
            kwargs['map_file_endpoint'] = old_file_url

        update_metadata_values(
            publication=publication,
            metadata_properties_to_refresh=metadata_properties_to_refresh,
            actor_name=workspace,
            **kwargs
        )
        csw_info = csw_module.get_metadata_comparison(publication)

    csw_url = next(iter(csw_info.keys()))
    metadata = csw_info[csw_url]
    assert metadata['graphic_url'] == old_thumbnail_url, (
        f"graphic_url did not match: expected '{old_thumbnail_url}', got '{metadata['graphic_url']}'"
    )

    if publ_type == 'map':
        assert metadata['map_file_endpoint'] == old_file_url, (
            f"map_file_endpoint did not match: expected '{old_file_url}', got '{metadata['map_file_endpoint']}'"
        )

    with app.app_context():
        migrate_func()
        csw_info = csw_module.get_metadata_comparison(publication)

    csw_url = next(iter(csw_info.keys()))
    metadata = csw_info[csw_url]

    with app.app_context():
        new_thumbnail_url = test_util.url_for_external(url_endpoint, uuid=test_uuid)
        new_file_url = test_util.url_for_external('rest_map_file.get', uuid=test_uuid) if publ_type == 'map' else None

    assert metadata['graphic_url'] == new_thumbnail_url, (
        f"graphic_url should be new format URL: expected '{new_thumbnail_url}', got '{metadata['graphic_url']}'"
    )

    if publ_type == 'map':
        assert metadata['map_file_endpoint'] == new_file_url, (
            f"map_file_endpoint should be new format URL: expected '{new_file_url}', got '{metadata['map_file_endpoint']}'"
        )

    with app.app_context():
        delete_func(uuid=test_uuid)
