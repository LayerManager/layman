import pytest

from layman import app
from layman.publication_relation import util
from test_tools import process_client
from ..data import ensure_publication
from ... import single_static_publication as data


@pytest.mark.parametrize('layer_workspace, layer_name, expected_maps', [
    (data.COMMON_WORKSPACE, 'post_blue_style', {(data.COMMON_WORKSPACE, 'post_internal_layer')}),
    (data.COMMON_WORKSPACE, 'faslughdauslf', set()),
    ('test1', 'post_blue_style', set()),
])
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_find_maps_containing_layer(layer_workspace, layer_name, expected_maps):
    ensure_publication(data.COMMON_WORKSPACE, process_client.LAYER_TYPE, 'post_blue_style')
    ensure_publication(data.COMMON_WORKSPACE, process_client.MAP_TYPE, 'post_internal_layer')
    with app.app_context():
        result_maps = util.find_maps_containing_layer(layer_workspace, layer_name)
    assert result_maps == expected_maps
