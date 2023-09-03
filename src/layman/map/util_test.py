import json
import pytest
from . import util as map_util


@pytest.mark.parametrize('json_path, exp_result', [
    pytest.param('sample/layman.map/internal_url.json', {
        ('testuser1', 'hranice', 1),
        ('testuser1', 'mista', 2),
    }, id='two_internal_wms_layers'),
    pytest.param('sample/layman.map/internal_url_two_wms_layers_in_one.json', {
        ('testuser1', 'hranice', 0),
        ('testuser1', 'mista', 0),
    }, id='two_internal_wms_layers_in_one'),
    pytest.param('sample/layman.map/internal_url_wms_workspace_in_layername.json', {
        ('testuser1', 'hranice', 0),
        ('testuser2', 'mista', 0),
    }, id='two_internal_wms_layers_in_one,workspace_in_layername'),
    pytest.param('sample/layman.map/internal_url_wms_layers_with_client_proxy.json', {
        ('testuser1', 'hranice', 0),
        ('testuser1', 'mista', 1),
    }, id='two_internal_wms_layers_with_client_proxy'),
    pytest.param('sample/layman.map/internal_url_wms_layer_in_wfs_workspace.json', {
        ('testuser1', 'hranice', 0),
    }, id='one_internal_wms_layer_in_wfs_workspace'),
    pytest.param('sample/layman.map/full.json', set(), id='external_layers_only'),
])
def test_get_layers_from_json(json_path, exp_result):
    with open(json_path, 'r', encoding="utf-8") as map_file:
        map_json = json.load(map_file)
    result = map_util.get_layers_from_json(map_json)
    assert result == exp_result
