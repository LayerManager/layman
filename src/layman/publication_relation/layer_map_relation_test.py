from test import process_client, util as test_util
from test.data import map as map_data, wfs as data_wfs
import pytest

from layman import app
from layman.map.filesystem import thumbnail


def assert_map_thumbnail(workspace, map, expected_thumbnail_path):
    process_client.wait_for_publication_status(workspace, process_client.MAP_TYPE, map)
    with app.app_context():
        thumbnail_path = thumbnail.get_map_thumbnail_path(workspace, map)
    diffs = test_util.compare_images(expected_thumbnail_path, thumbnail_path)
    assert diffs < 10, expected_thumbnail_path


@pytest.mark.usefixtures('ensure_layman')
def test_map_refresh_after_layer_change():
    workspace = 'test_map_refresh_after_layer_change_workspace'
    layer = 'test_map_refresh_after_layer_change_layer'
    map = 'test_map_refresh_after_layer_change_map'
    bbox = (1571000.0, 6268800.0, 1572590.8542062, 6269876.33561699)

    process_client.publish_workspace_layer(workspace, layer)

    map_file = map_data.create_map_with_internal_layers_file([(workspace, layer)], extent_3857=bbox)
    process_client.publish_workspace_map(workspace, map, file_paths=[map_file])

    assert_map_thumbnail(workspace, map, f'/code/test/data/thumbnail/map_with_internal_layer_basic.png')

    # Test refresh map thumbnail after layer WFS-T query
    data_xml = data_wfs.get_wfs20_insert_points(workspace, layer, )
    process_client.post_wfst(data_xml)
    process_client.wait_for_publication_status(workspace, process_client.LAYER_TYPE, layer)
    assert_map_thumbnail(workspace, map, f'/code/test/data/thumbnail/map_with_internal_layer_basic_after_wfst.png')

    # Test refresh map thumbnail after patch layer
    process_client.patch_workspace_layer(workspace, layer, file_paths=['sample/layman.layer/small_layer.geojson'])
    process_client.wait_for_publication_status(workspace, process_client.LAYER_TYPE, layer)
    assert_map_thumbnail(workspace, map, f'/code/test/data/thumbnail/map_with_internal_layer_basic.png')

    process_client.delete_workspace_map(workspace, map)
    process_client.delete_workspace_layer(workspace, layer)
