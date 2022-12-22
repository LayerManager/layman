import copy
import math
from urllib import parse

import crs as crs_def
from layman import app, settings, util as layman_util
from layman.common import bbox as bbox_util
from layman.layer.geoserver import wfs, wms
from test_tools import geoserver_client, process_client, assert_util


def feature_spatial_precision(workspace, publ_type, name, *, feature_id, crs, exp_coordinates, precision):
    assert publ_type == process_client.LAYER_TYPE

    feature_collection = geoserver_client.get_features(workspace, name, crs=crs)
    feature = next(f for f in feature_collection['features'] if f['properties']['point_id'] == feature_id)
    for idx, coordinate in enumerate(feature['geometry']['coordinates']):
        assert abs(coordinate - exp_coordinates[idx]) <= precision, f"{crs}: expected coordinates={exp_coordinates}, found coordinates={feature['geometry']['coordinates']}"


def wms_spatial_precision(workspace, publ_type, name, *, crs, extent, img_size, wms_version, obtained_file_path,
                          expected_file_path, diff_line_width=None, pixel_diff_limit=None, time=None):
    assert publ_type == process_client.LAYER_TYPE
    assert diff_line_width is None or pixel_diff_limit is None, f'diff_line_width={diff_line_width}, pixel_diff_limit={pixel_diff_limit}'
    assert diff_line_width is not None or pixel_diff_limit is not None, f'diff_line_width={diff_line_width}, pixel_diff_limit={pixel_diff_limit}'

    crs_name = {
        '1.1.1': 'SRS',
        '1.3.0': 'CRS',
    }[wms_version]

    with app.app_context():
        publ_info = layman_util.get_publication_info(workspace, publ_type, name, {'keys': ['native_crs', 'style_type',
                                                                                           'file']})
        native_crs = publ_info['native_crs']
        style_type = publ_info['_style_type']

    query_params = {
        'SERVICE': 'WMS',
        'VERSION': wms_version,
        'REQUEST': 'GetMap',
        'FORMAT': 'image/png',
        'TRANSPARENT': 'true',
        # 'STYLES': None,
        'LAYERS': f'{workspace}_wms:{name}',
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

    geoserver_url = f'{settings.LAYMAN_GS_URL}/{workspace}_wms/wms?{parse.urlencode(gs_query_params)}'
    layman_without_workspace_url = f'http://{settings.LAYMAN_SERVER_NAME}/geoserver/wms?{parse.urlencode(query_params)}'
    query_params['LAYERS'] = name
    layman_with_workspace_url = f'http://{settings.LAYMAN_SERVER_NAME}/geoserver/{workspace}_wms/wms?{parse.urlencode(query_params)}'

    if diff_line_width is not None:
        circle_diameter = 30
        circle_perimeter = circle_diameter * math.pi
        num_circles = 5
        pixel_diff_limit = circle_perimeter * num_circles * diff_line_width

    for url in [geoserver_url,
                layman_with_workspace_url,
                layman_without_workspace_url,
                ]:
        assert_util.assert_same_images(url, obtained_file_path, expected_file_path, pixel_diff_limit)


def wfs_bbox(workspace, publ_type, name, *, exp_bbox, precision=0.00001):
    assert publ_type == process_client.LAYER_TYPE

    wfs_layer = f"{workspace}:{name}"
    with app.app_context():
        wfs_inst = wfs.get_wfs_proxy(workspace)
    bbox = wfs_inst.contents[wfs_layer].boundingBoxWGS84
    assert_util.assert_same_bboxes(exp_bbox, bbox, precision)
    assert bbox_util.contains_bbox(bbox, exp_bbox, precision=precision / 10000)


def wms_geographic_bbox(workspace, publ_type, name, *, exp_bbox, precision=0.00001, contains=True):
    assert publ_type == process_client.LAYER_TYPE

    with app.app_context():
        wms_inst = wms.get_wms_proxy(workspace)
    wms_layer = wms_inst.contents[name]
    bbox = wms_layer.boundingBoxWGS84
    assert_util.assert_same_bboxes(exp_bbox, bbox, precision)
    if contains:
        assert bbox_util.contains_bbox(bbox, exp_bbox, precision=precision / 10000)


def wms_bbox(workspace, publ_type, name, *, exp_bbox, crs, precision=0.00001, contains=True):
    assert publ_type == process_client.LAYER_TYPE

    with app.app_context():
        wms_inst = wms.get_wms_proxy(workspace)
    wms_layer = wms_inst.contents[name]
    bbox = next(bbox[:4] for bbox in wms_layer.crs_list if bbox[4] == crs)
    assert_util.assert_same_bboxes(exp_bbox, bbox, precision)
    if contains:
        assert bbox_util.contains_bbox(bbox, exp_bbox, precision=precision / 10000)


def wms_legend(workspace, publ_type, name, *, exp_legend, obtained_file_path):
    assert publ_type == process_client.LAYER_TYPE

    with app.app_context():
        wms_inst = wms.get_wms_proxy(workspace)
    wms_layer = wms_inst.contents[name]
    legend_url = next(iter(wms_layer.styles.values()))['legend']
    assert_util.assert_same_images(legend_url, obtained_file_path, exp_legend, 0)
