import math
import requests

import crs as crs_def
from layman import app, settings, util as layman_util
from layman.common import bbox as bbox_util
from layman.layer.geoserver import wfs, wms
from test_tools import util as test_util, geoserver_client, process_client, assert_util


def workspace_wms_1_3_0_capabilities_available(workspace):
    with app.app_context():
        internal_wms_url = test_util.url_for('geoserver_proxy_bp.proxy', subpath=workspace + settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX + '/ows')

    r_wms = requests.get(internal_wms_url, params={
        'service': 'WMS',
        'request': 'GetCapabilities',
        'version': '1.3.0',
    })
    assert r_wms.status_code == 200


def workspace_wfs_2_0_0_capabilities_available_if_vector(workspace, publ_type, name):
    with app.app_context():
        internal_wfs_url = test_util.url_for('geoserver_proxy_bp.proxy', subpath=workspace + '/wfs')

    with app.app_context():
        file_info = layman_util.get_publication_info(workspace, publ_type, name, {'keys': ['file']})['file']
    file_type = file_info['file_type']
    if file_type == settings.FILE_TYPE_VECTOR:
        r_wfs = requests.get(internal_wfs_url, params={
            'service': 'WFS',
            'request': 'GetCapabilities',
            'version': '2.0.0',
        })
        assert r_wfs.status_code == 200


def feature_spatial_precision(workspace, publ_type, name, *, feature_id, crs, exp_coordinates, precision):
    assert publ_type == process_client.LAYER_TYPE

    feature_collection = geoserver_client.get_features(workspace, name, crs=crs)
    feature = next(f for f in feature_collection['features'] if f['properties']['point_id'] == feature_id)
    for idx, coordinate in enumerate(feature['geometry']['coordinates']):
        assert abs(coordinate - exp_coordinates[idx]) <= precision, f"{crs}: expected coordinates={exp_coordinates}, found coordinates={feature['geometry']['coordinates']}"


def wms_spatial_precision(workspace, publ_type, name, *, crs, extent, img_size, wms_version, diff_line_width, obtained_file_path,
                          expected_file_path, ):
    assert publ_type == process_client.LAYER_TYPE

    crs_name = {
        '1.1.1': 'SRS',
        '1.3.0': 'CRS',
    }[wms_version]

    with app.app_context():
        publ_info = layman_util.get_publication_info(workspace, publ_type, name, {'keys': ['native_crs', 'style_type']})
        native_crs = publ_info['native_crs']
        style_type = publ_info['style_type']
    buffer_parameter = '' if native_crs != crs_def.EPSG_5514 or crs != crs_def.EPSG_3857 or style_type != 'sld' else '&BUFFER=100000'

    url_part = f'/{workspace}_wms/wms?SERVICE=WMS&VERSION={wms_version}&REQUEST=GetMap&FORMAT=image%2Fpng&TRANSPARENT=true&STYLES&LAYERS={workspace}_wms%3A{name}&FORMAT_OPTIONS=antialias%3Afull&{crs_name}={crs}&WIDTH={img_size[0]}&HEIGHT={img_size[1]}&BBOX={"%2C".join((str(c) for c in extent))}'
    geoserver_url = f'{settings.LAYMAN_GS_URL}{url_part}{buffer_parameter}'
    layman_url = f'http://{settings.LAYMAN_SERVER_NAME}/geoserver{url_part}'

    circle_diameter = 30
    circle_perimeter = circle_diameter * math.pi
    num_circles = 5
    pixel_diff_limit = circle_perimeter * num_circles * diff_line_width

    assert_util.assert_same_images(layman_url, obtained_file_path, expected_file_path, pixel_diff_limit)
    assert_util.assert_same_images(geoserver_url, obtained_file_path, expected_file_path, pixel_diff_limit)


def wfs_bbox(workspace, publ_type, name, *, exp_bbox, precision=0.00001):
    assert publ_type == process_client.LAYER_TYPE

    wfs_layer = f"{workspace}:{name}"
    with app.app_context():
        wfs_get_capabilities = wfs.get_wfs_proxy(workspace)
    bbox = wfs_get_capabilities.contents[wfs_layer].boundingBoxWGS84
    assert_util.assert_same_bboxes(exp_bbox, bbox, precision)
    assert bbox_util.contains_bbox(bbox, exp_bbox, precision=precision / 10000)


def wms_geographic_bbox(workspace, publ_type, name, *, exp_bbox, precision=0.00001):
    assert publ_type == process_client.LAYER_TYPE

    with app.app_context():
        wms_get_capabilities = wms.get_wms_proxy(workspace)
    wms_layer = wms_get_capabilities.contents[name]
    bbox = wms_layer.boundingBoxWGS84
    assert_util.assert_same_bboxes(exp_bbox, bbox, precision)
    assert bbox_util.contains_bbox(bbox, exp_bbox, precision=precision / 10000)


def wms_bbox(workspace, publ_type, name, *, exp_bbox, crs, precision=0.00001):
    assert publ_type == process_client.LAYER_TYPE

    with app.app_context():
        wms_get_capabilities = wms.get_wms_proxy(workspace)
    wms_layer = wms_get_capabilities.contents[name]
    bbox = next(bbox[:4] for bbox in wms_layer.crs_list if bbox[4] == crs)
    assert_util.assert_same_bboxes(exp_bbox, bbox, precision)
    assert bbox_util.contains_bbox(bbox, exp_bbox, precision=precision / 10000)
