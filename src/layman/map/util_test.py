import pytest
from layman.util import XForwardedClass
from . import util as map_util


@pytest.mark.parametrize('json_path, exp_result', [
    pytest.param('sample/layman.map/internal_url.json', [
        ('testuser1', 'hranice', 1),
        ('testuser1', 'mista', 2),
        ('testuser1', 'hranice', 3),
    ], id='two_internal_wms_layers,one_internal_wfs_layer'),
    pytest.param('sample/layman.map/internal_url_two_wms_layers_in_one.json', [
        ('testuser1', 'hranice', 0),
        ('testuser1', 'mista', 0),
    ], id='two_internal_wms_layers_in_one'),
    pytest.param('sample/layman.map/internal_url_wms_workspace_in_layername.json', [
        ('testuser1', 'hranice', 0),
        ('testuser2', 'mista', 0),
    ], id='two_internal_wms_layers_in_one,workspace_in_layername'),
    pytest.param('sample/layman.map/internal_url_two_wms_layers_with_client_proxy.json', [
        ('testuser1', 'hranice', 0),
        ('testuser1', 'mista', 1),
    ], id='two_internal_wms_layers_with_client_proxy'),
    pytest.param('sample/layman.map/internal_url_wms_layer_in_wfs_workspace.json', [
        ('testuser1', 'hranice', 0),
    ], id='one_internal_wms_layer_in_wfs_workspace'),
    pytest.param('sample/layman.map/internal_url_wfs_workspace_in_layername.json', [
        ('testuser1', 'hranice', 0),
    ], id='one_internal_wfs_layer,workspace_in_layername'),
    pytest.param('sample/layman.map/internal_external_edge_cases.json', [], id='empty_edge_cases'),
    pytest.param('sample/layman.map/full.json', [], id='external_layers_only'),
])
def test_get_layers_from_json(json_path, exp_result):
    with open(json_path, 'r', encoding="utf-8") as map_file:
        map_json = map_util.check_file(map_file)
    x_forwarded_items = XForwardedClass(proto='https', host='laymanproxy.com', prefix='/some-proxy-path')
    result = map_util.get_layers_from_json(map_json, x_forwarded_items=x_forwarded_items)
    assert result == exp_result
