import os
import time
from test import process_client
from test.data import wfs as wfs_data_util
import requests
from owslib.wms import WebMapService
import pytest
from layman import settings
from layman.layer.geoserver import wms as gs_wms


def get_shp_file_paths(shp_file_path):
    extensions = ['dbf', 'prj', 'qpj', 'shx']
    root, _ = os.path.splitext(shp_file_path)
    result = [f"{root}.{ext}" for ext in extensions]
    result.append(shp_file_path)
    return result


def assert_non_empty_bbox(bbox):
    assert bbox[0] < bbox[2] and bbox[1] < bbox[3]


def assert_wms_layer(workspace, layername, exp_title):
    wms = WebMapService(gs_wms.get_wms_url(workspace), gs_wms.VERSION)
    assert layername in wms.contents
    wms_layer = wms[layername]
    assert wms_layer.title == exp_title
    assert_non_empty_bbox(wms_layer.boundingBox)
    assert_non_empty_bbox(wms_layer.boundingBoxWGS84)
    return wms_layer


def wfs_t_insert_point(workspace, layername):
    wfs_t_data = wfs_data_util.get_wfs20_insert_points(workspace, layername)
    wfs_t_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/{workspace}/wfs?request=Transaction"
    wfs_t_headers = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
    }
    r = requests.post(wfs_t_url,
                      data=wfs_t_data,
                      headers=wfs_t_headers)
    assert r.status_code == 200, r.text


@pytest.mark.parametrize('layername, file_paths', [
    ('empty', get_shp_file_paths('sample/layman.layer/empty.shp')),
    ('single_point', get_shp_file_paths('sample/layman.layer/single_point.shp')),
])
@pytest.mark.usefixtures('ensure_layman')
def test_empty_shapefile(layername, file_paths):
    workspace = 'test_empty_bbox_workspace'
    title = layername

    process_client.publish_workspace_layer(workspace, layername, file_paths=file_paths)

    wms_layer = assert_wms_layer(workspace, layername, title)
    native_bbox = wms_layer.boundingBox
    wgs_bbox = wms_layer.boundingBoxWGS84

    title = 'new title'
    process_client.patch_workspace_layer(workspace, layername, title=title)
    wms_layer = assert_wms_layer(workspace, layername, title)
    assert wms_layer.boundingBox == native_bbox
    assert wms_layer.boundingBoxWGS84 == wgs_bbox

    wfs_t_insert_point(workspace, layername)
    wms_layer = assert_wms_layer(workspace, layername, title)
    assert wms_layer.boundingBox == native_bbox
    assert wms_layer.boundingBoxWGS84 == wgs_bbox

    time.sleep(5)

    process_client.delete_workspace_layer(workspace, layername)
