import os
from owslib.wms import WebMapService
import pytest

from layman.layer.geoserver import wms as gs_wms
from test_tools import process_client
from test_tools.data import wfs as wfs_data_util
from test_tools.mock.layman_classes import LayerMock


def get_shp_file_paths(shp_file_path):
    extensions = ['dbf', 'prj', 'qpj', 'shx']
    root, _ = os.path.splitext(shp_file_path)
    result = [f"{root}.{ext}" for ext in extensions]
    result.append(shp_file_path)
    return result


def assert_non_empty_bbox(bbox):
    assert bbox[0] < bbox[2] and bbox[1] < bbox[3]


def assert_wms_layer(uuid, exp_title):
    layer = LayerMock(uuid=uuid, layer_tuple=None)
    gs_layername = layer.gs_ids.wms
    wms = WebMapService(gs_wms.get_wms_url(), gs_wms.VERSION)
    assert gs_layername.name in wms.contents
    wms_layer = wms[gs_layername.name]
    assert wms_layer.title == exp_title
    assert_non_empty_bbox(wms_layer.boundingBox)
    assert_non_empty_bbox(wms_layer.boundingBoxWGS84)
    return wms_layer


def wfs_t_insert_point(*, uuid):
    layer = LayerMock(uuid=uuid, layer_tuple=None)
    gs_layername = layer.gs_ids.wfs
    wfs_t_data = wfs_data_util.get_wfs20_insert_points(gs_layername.workspace, gs_layername.name)
    process_client.post_wfst(wfs_t_data, workspace=gs_layername.workspace)


@pytest.mark.parametrize('layername, file_paths', [
    ('empty', get_shp_file_paths('sample/layman.layer/empty.shp')),
    ('single_point', get_shp_file_paths('sample/layman.layer/single_point.shp')),
])
@pytest.mark.usefixtures('ensure_layman')
def test_empty_shapefile(layername, file_paths):
    workspace = 'test_empty_bbox_workspace'
    title = layername

    uuid = process_client.publish_workspace_layer(workspace, layername, file_paths=file_paths)['uuid']

    wms_layer = assert_wms_layer(uuid, title)
    native_bbox = wms_layer.boundingBox
    wgs_bbox = wms_layer.boundingBoxWGS84

    title = 'new title'
    process_client.patch_workspace_layer(workspace, layername, title=title)
    wms_layer = assert_wms_layer(uuid, title)
    assert wms_layer.boundingBox == native_bbox
    assert wms_layer.boundingBoxWGS84 == wgs_bbox

    wfs_t_insert_point(uuid=uuid)
    wms_layer = assert_wms_layer(uuid, title)
    assert wms_layer.boundingBox == native_bbox
    assert wms_layer.boundingBoxWGS84 == wgs_bbox

    process_client.delete_workspace_layer(workspace, layername)
