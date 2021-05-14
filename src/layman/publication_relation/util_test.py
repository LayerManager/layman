import os
from test import process_client
import pytest

from layman import app
from . import util


class TestFindMapsContainingLayer:
    workspace = 'test_find_maps_containing_layer_workspace'
    directory = f'/code/test/data/maps/publication_relation_util_test/'
    maps = set()
    layers = [('testuser1', 'mista')]

    @pytest.fixture(scope="class")
    def provide_data(self):
        for workspace, layer in self.layers:
            process_client.publish_workspace_layer(workspace, layer)
        for file in os.listdir(self.directory):
            mapname = os.path.splitext(file)[0]
            file_path = os.path.join(self.directory, file)
            process_client.publish_workspace_map(self.workspace, mapname, file_paths=[file_path])
            self.maps.add((self.workspace, mapname))
        yield
        for map_workspace, map_name in self.maps:
            process_client.delete_workspace_map(map_workspace, map_name)
        for workspace, layer in self.layers:
            process_client.delete_workspace_layer(workspace, layer)

    @staticmethod
    @pytest.mark.parametrize('layer_workspace, layer_name, expected_maps', [
        ('testuser1', 'mista', {(workspace, 'map_1')}),
        ('testuser1', 'faslughdauslf', set()),
        ('test1', 'mista', set()),
    ])
    @pytest.mark.usefixtures('ensure_layman', 'provide_data')
    def test_find_maps_containing_layer(layer_workspace, layer_name, expected_maps):
        with app.app_context():
            result_maps = util.find_maps_containing_layer(layer_workspace, layer_name)
        assert result_maps == expected_maps
