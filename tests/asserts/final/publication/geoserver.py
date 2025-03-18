import copy
from urllib import parse

import crs as crs_def
from geoserver import util as gs_util
from layman import app, settings, util as layman_util
from layman.common import bbox as bbox_util
from layman.layer.geoserver import wfs, wms, GEOSERVER_WMS_WORKSPACE, GEOSERVER_WFS_WORKSPACE, GeoserverIds
from test_tools import geoserver_client, process_client, assert_util
from . import geoserver_util


def feature_spatial_precision(workspace, publ_type, name, *, feature_id, crs, exp_coordinates, precision):
    assert publ_type == process_client.LAYER_TYPE
    with app.app_context():
        uuid = layman_util.get_publication_uuid(workspace, publ_type, name)
    gs_layername = GeoserverIds(uuid=uuid).wfs

    feature_collection = geoserver_client.get_features(gs_layername.workspace, gs_layername.name, crs=crs)
    feature = next(f for f in feature_collection['features'] if f['properties']['point_id'] == feature_id)
    for idx, coordinate in enumerate(feature['geometry']['coordinates']):
        assert abs(coordinate - exp_coordinates[idx]) <= precision, f"{crs}: expected coordinates={exp_coordinates}, found coordinates={feature['geometry']['coordinates']}"


def wms_spatial_precision(workspace, publ_type, name, *, crs, extent, img_size, wms_version, obtained_file_path,
                          expected_file_path, pixel_diff_limit=None, time=None):
    assert publ_type == process_client.LAYER_TYPE

    crs_name = {
        '1.1.1': 'SRS',
        '1.3.0': 'CRS',
    }[wms_version]

    with app.app_context():
        publ_info = layman_util.get_publication_info(workspace, publ_type, name, {'keys': ['native_crs', 'style_type',
                                                                                           'file', 'uuid']})
    native_crs = publ_info['native_crs']
    style_type = publ_info['_style_type']
    wms_layername = GeoserverIds(uuid=publ_info['uuid'], ).wms

    query_params = {
        'SERVICE': 'WMS',
        'VERSION': wms_version,
        'REQUEST': 'GetMap',
        'FORMAT': 'image/png',
        'TRANSPARENT': 'true',
        # 'STYLES': None,
        'LAYERS': f'{wms_layername.workspace}:{wms_layername.name}',
        'FORMAT_OPTIONS': 'antialias:full',
        crs_name: crs,
        'WIDTH': img_size[0],
        'HEIGHT': img_size[1],
        'BBOX': ",".join((str(c) for c in extent)),
    }

    if time:
        query_params['TIME'] = time

    gs_query_params = copy.deepcopy(query_params)
    if native_crs == crs_def.EPSG_5514 and crs == crs_def.CRS_84 and style_type == 'sld':
        gs_query_params[crs_name] = crs_def.EPSG_4326
        if wms_version == '1.3.0':
            bbox = [extent[1], extent[0], extent[3], extent[2]]
            gs_query_params['BBOX'] = ",".join((str(c) for c in bbox))

    geoserver_url = f'{settings.LAYMAN_GS_URL}{wms_layername.workspace}/wms?{parse.urlencode(gs_query_params)}'
    layman_without_workspace_url = f'http://{settings.LAYMAN_SERVER_NAME}/geoserver/wms?{parse.urlencode(query_params)}'
    query_params['LAYERS'] = wms_layername.name
    layman_with_workspace_url = f'http://{settings.LAYMAN_SERVER_NAME}/geoserver/{wms_layername.workspace}/wms?{parse.urlencode(query_params)}'

    for url in [geoserver_url,
                layman_with_workspace_url,
                layman_without_workspace_url,
                ]:
        assert_util.assert_same_images(url, obtained_file_path, expected_file_path, pixel_diff_limit)


def wfs_bbox(workspace, publ_type, name, *, exp_bbox, precision=0.00001):
    assert publ_type == process_client.LAYER_TYPE
    with app.app_context():
        uuid = layman_util.get_publication_uuid(workspace, publ_type, name)
        gs_layername = GeoserverIds(uuid=uuid).wfs
        wfs_inst = wfs.get_wfs_proxy()
    wfs_layer = f"{gs_layername.workspace}:{gs_layername.name}"

    bbox = wfs_inst.contents[wfs_layer].boundingBoxWGS84
    assert_util.assert_same_bboxes(exp_bbox, bbox, precision)
    assert bbox_util.contains_bbox(bbox, exp_bbox, precision=precision / 10000)


def wms_geographic_bbox(workspace, publ_type, name, *, exp_bbox, precision=0.00001, contains=True):
    assert publ_type == process_client.LAYER_TYPE

    with app.app_context():
        uuid = layman_util.get_publication_uuid(workspace, process_client.LAYER_TYPE, name)
        gs_layername = GeoserverIds(uuid=uuid).wms
        wms_inst = wms.get_wms_proxy()
    wms_layer = wms_inst.contents[gs_layername.name]
    bbox = wms_layer.boundingBoxWGS84
    assert_util.assert_same_bboxes(exp_bbox, bbox, precision)
    if contains:
        assert bbox_util.contains_bbox(bbox, exp_bbox, precision=precision / 10000)


def wms_bbox(workspace, publ_type, name, *, exp_bbox, crs, precision=0.00001, contains=True):
    assert publ_type == process_client.LAYER_TYPE

    with app.app_context():
        uuid = layman_util.get_publication_uuid(workspace, process_client.LAYER_TYPE, name)
        gs_layername = GeoserverIds(uuid=uuid).wms
        wms_inst = wms.get_wms_proxy()
    wms_layer = wms_inst.contents[gs_layername.name]
    bbox = next(bbox[:4] for bbox in wms_layer.crs_list if bbox[4] == crs)
    assert_util.assert_same_bboxes(exp_bbox, bbox, precision)
    if contains:
        assert bbox_util.contains_bbox(bbox, exp_bbox, precision=precision / 10000)


def wms_legend(workspace, publ_type, name, *, exp_legend, obtained_file_path):
    assert publ_type == process_client.LAYER_TYPE

    with app.app_context():
        uuid = layman_util.get_publication_uuid(workspace, process_client.LAYER_TYPE, name)
        gs_layername = GeoserverIds(uuid=uuid).wms
        wms_inst = wms.get_wms_proxy()
    wms_layer = wms_inst.contents[gs_layername.name]
    legend_url = next(iter(wms_layer.styles.values()))['legend']
    assert_util.assert_same_images(legend_url, obtained_file_path, exp_legend, 0)


def is_complete_in_internal_workspace_wms(workspace, publ_type, name):
    assert publ_type == process_client.LAYER_TYPE

    with app.app_context():
        uuid = layman_util.get_publication_uuid(workspace, process_client.LAYER_TYPE, name)
    gs_layername = GeoserverIds(uuid=uuid).wms
    wms_inst = wms.get_wms_proxy()

    geoserver_util.is_complete_in_workspace_wms_instance(wms_inst, gs_layername.name, validate_metadata_url=False)


def assert_workspace_stores(workspace, *, exp_stores=None, exp_existing_stores=None, exp_deleted_stores=None):
    exp_existing_stores = exp_existing_stores or []
    exp_deleted_stores = exp_deleted_stores or []
    stores = gs_util.get_db_stores(geoserver_workspace=workspace,
                                   auth=settings.LAYMAN_GS_AUTH,
                                   )
    store_names = {store['name'] for store in stores['dataStores']['dataStore']}
    if exp_stores:
        assert store_names == exp_stores, f'workspace={workspace}, store_names={store_names}, exp_stores={exp_stores}'
    for store in exp_existing_stores:
        assert store in store_names, f'workspace={workspace}, store_names={store_names}, superfluous store={store}'
    for store in exp_deleted_stores:
        assert store not in store_names, f'workspace={workspace}, store_names={store_names}, missing store={store}'


def assert_stores(exp_wfs_stores=None, exp_existing_wfs_stores=None, exp_deleted_wfs_stores=None,
                  exp_wms_stores=None, exp_existing_wms_stores=None, exp_deleted_wms_stores=None,):
    assert_workspace_stores(workspace=GEOSERVER_WFS_WORKSPACE, exp_stores=exp_wfs_stores,
                            exp_existing_stores=exp_existing_wfs_stores, exp_deleted_stores=exp_deleted_wfs_stores)
    assert_workspace_stores(workspace=GEOSERVER_WMS_WORKSPACE, exp_stores=exp_wms_stores,
                            exp_existing_stores=exp_existing_wms_stores, exp_deleted_stores=exp_deleted_wms_stores)
