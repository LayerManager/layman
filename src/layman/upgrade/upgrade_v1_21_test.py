import json
from urllib.parse import urljoin
import requests
import pytest

from db import util as db_util
from geoserver import GS_REST_WORKSPACES, GS_REST_TIMEOUT, util as gs_common_util
from layman import app, settings, util as layman_util
from layman.layer.geoserver import wms, util as gs_util
from test_tools import process_client, util as test_util
from tests import Publication
from tests.asserts.final.publication import util as asserts_util
from tests.dynamic_data.publications import common_publications
from . import upgrade_v1_21

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


@pytest.mark.parametrize('publ_type, publ_name, rest_args, exp_wfs_wms_status', [
    pytest.param(
        process_client.LAYER_TYPE,
        'test_layer',
        {},
        settings.EnumWfsWmsStatus.AVAILABLE,
        id='layer_available',
    ),
    pytest.param(
        process_client.LAYER_TYPE,
        'test_updating_layer',
        {
            'compress': True,
            'with_chunks': True,
            'do_not_upload_chunks': True,
            'raise_if_not_complete': False,
        },
        settings.EnumWfsWmsStatus.NOT_AVAILABLE,
        id='layer_updating',
    ),
    pytest.param(
        process_client.LAYER_TYPE,
        'test_failed_layer',
        {
            'file_paths': [
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.cpg',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.dbf',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shx',
            ],
            'compress': True,
            'with_chunks': True,
            'raise_if_not_complete': False,
        },
        settings.EnumWfsWmsStatus.NOT_AVAILABLE,
        id='layer_not_available',
    ),
    pytest.param(
        process_client.LAYER_TYPE,
        'test_raster_layer',
        common_publications.LAYER_RASTER.definition,
        settings.EnumWfsWmsStatus.AVAILABLE,
        id='layer_raster_available',
    ),
    pytest.param(
        process_client.LAYER_TYPE,
        'layer_vector_qml_layer',
        common_publications.LAYER_VECTOR_QML.definition,
        settings.EnumWfsWmsStatus.AVAILABLE,
        id='layer_vector_qml_available',
    ),
    pytest.param(
        process_client.MAP_TYPE,
        'test_map',
        {},
        settings.EnumWfsWmsStatus.AVAILABLE,
        id='map',
    ),
])
@pytest.mark.usefixtures('ensure_layman')
def test_wfs_wms_status(publ_type, publ_name, rest_args, exp_wfs_wms_status):
    workspace = 'test_wfs_wms_status_workspace'

    process_client.publish_workspace_publication(publ_type, workspace, publ_name, **rest_args)

    statement = f'''ALTER TABLE {DB_SCHEMA}.publications DROP COLUMN wfs_wms_status;'''
    with app.app_context():
        db_util.run_statement(statement)

        upgrade_v1_21.adjust_db_for_wfs_wms_status()
        upgrade_v1_21.adjust_publications_wfs_wms_status()

    query = f'''select p.wfs_wms_status
    from {DB_SCHEMA}.publications p left join
     {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
where w.name = %s
  and p.name = %s
  and p.type = %s
;'''
    with app.app_context():
        wfs_wms_status = db_util.run_query(query, (workspace, publ_name, publ_type))[0][0]
    if publ_type == process_client.LAYER_TYPE:
        assert wfs_wms_status == exp_wfs_wms_status.value, f'publication={publ_type}:{workspace}.{publ_name}, wfs_wms_status={wfs_wms_status}'
    else:
        assert wfs_wms_status is None, f'publication={publ_type}:{workspace}.{publ_name}, wfs_wms_status={wfs_wms_status}'

    process_client.delete_workspace_publication(publ_type, workspace, publ_name)


@pytest.mark.usefixtures('ensure_layman')
def test_adjust_layer_metadata_url_on_gs():
    workspace = 'test_adjust_metadata_url_workspace'
    auth = settings.LAYMAN_GS_AUTH

    layers = [
        ('vector_sld', common_publications.LAYER_VECTOR_SLD.definition),
        ('vector_qml', common_publications.LAYER_VECTOR_QML.definition),
        ('raster', common_publications.LAYER_RASTER.definition),
    ]

    for layer, layer_def in layers:
        process_client.publish_workspace_publication(process_client.LAYER_TYPE, workspace, layer, **layer_def)
        with app.app_context():
            publ_info = layman_util.get_publication_info(workspace, process_client.LAYER_TYPE, layer,
                                                         context={'keys': {'geodata_type', 'style_type', 'image_mosaic',
                                                                           'original_data_source'}})
        wms_workspace = wms.get_geoserver_workspace(workspace)

        if publ_info['geodata_type'] == settings.GEODATA_TYPE_RASTER:
            store_name = wms.get_image_mosaic_store_name(layer) if publ_info['image_mosaic'] else wms.get_geotiff_store_name(layer)
            wms_coverage = gs_common_util.get_coverage(wms_workspace, store_name, layer, gs_rest_workspaces=GS_REST_WORKSPACES)
            wms_coverage['metadataLinks'] = {}
            wms_body = {"coverage": wms_coverage}
            wms_url = urljoin(GS_REST_WORKSPACES, f'{wms_workspace}/coveragestores/{store_name}/coverages/{layer}')
        elif publ_info['geodata_type'] == settings.GEODATA_TYPE_VECTOR:
            if publ_info['_style_type'] == 'sld':
                store_name = gs_util.get_external_db_store_name(layer) if publ_info[
                    'original_data_source'] == settings.EnumOriginalDataSource.TABLE.value else gs_common_util.DEFAULT_DB_STORE_NAME
                wms_feature_type = gs_common_util.get_feature_type(wms_workspace, store_name, layer, gs_rest_workspaces=GS_REST_WORKSPACES)
                wms_feature_type['metadataLinks'] = {}
                wms_body = {"featureType": wms_feature_type}
                wms_url = urljoin(GS_REST_WORKSPACES, f'{wms_workspace}/datastores/{store_name}/featuretypes/{layer}')
            elif publ_info['_style_type'] == 'qml':
                wms_layer = gs_common_util.get_wms_layer(wms_workspace, layer, auth=auth)
                wms_layer['metadataLinks'] = {}
                wms_body = {"wmsLayer": wms_layer}
                wms_url = urljoin(GS_REST_WORKSPACES, f'{wms_workspace}/wmslayers/{layer}')
            else:
                raise NotImplementedError(f"Unknown style type: {publ_info['_style_type']}")

            # WFS
            wfs_store = gs_util.get_external_db_store_name(layer) if publ_info[
                'original_data_source'] == settings.EnumOriginalDataSource.TABLE.value else gs_common_util.DEFAULT_DB_STORE_NAME

            wfs_inner_body = gs_common_util.get_feature_type(workspace, wfs_store, layer, gs_rest_workspaces=GS_REST_WORKSPACES)
            wfs_inner_body['metadataLinks'] = {}
            wfs_body = {"featureType": wfs_inner_body}
            response = requests.put(
                urljoin(GS_REST_WORKSPACES, f'{workspace}/datastores/{wfs_store}/featuretypes/{layer}'),
                data=json.dumps(wfs_body),
                headers=gs_common_util.headers_json,
                auth=auth,
                timeout=GS_REST_TIMEOUT,
            )
            response.raise_for_status()

            # Validate MetadataLinks emptiness
            with app.app_context():
                wfs_url = test_util.url_for('geoserver_proxy_bp.proxy',
                                            subpath=f'{workspace}/ows')
            wfs_inst = gs_util.wfs_proxy(wfs_url, version='2.0.0')
            wfs_layer = wfs_inst.contents[f'{workspace}:{layer}']
            assert len(wfs_layer.metadataUrls) == 0, f'layer={layer}, wfs_layer.metadataUrls={wfs_layer.metadataUrls}'
        else:
            raise NotImplementedError(f"Unknown geodata type: {publ_info['geodata_type']}")

        # WMS
        response = requests.put(
            wms_url,
            data=json.dumps(wms_body),
            headers=gs_common_util.headers_json,
            auth=auth,
            timeout=GS_REST_TIMEOUT,
        )
        response.raise_for_status()

        # Validate MetadataLinks emptiness
        with app.app_context():
            wms_url = test_util.url_for('geoserver_proxy_bp.proxy',
                                        subpath=f'{workspace}{settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX}/ows')
        wms_inst = gs_util.wms_proxy(wms_url, version='1.3.0')
        wms_layer = wms_inst.contents[layer]
        assert len(wms_layer.metadataUrls) == 0, f'layer={layer}, wms_layer.metadataUrls={wms_layer.metadataUrls}'

    with app.app_context():
        upgrade_v1_21.adjust_layer_metadata_url_on_gs()

    for layer, _ in layers:
        asserts_util.is_publication_valid_and_complete(Publication(workspace=workspace,
                                                                   type=process_client.LAYER_TYPE,
                                                                   name=layer))

    process_client.delete_workspace_layers(workspace)
