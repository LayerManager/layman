import pytest
from layman import app
from layman.layer.filesystem import thumbnail as layer_thumbnail
from layman.map.filesystem import thumbnail as map_thumbnail
from test_tools import util as test_util, process_client
from ... import single_static_publication as data
from ..data import ensure_publication


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('ensure_layman')
def test_thumbnail(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    thumbnail_path_method = {process_client.LAYER_TYPE: layer_thumbnail.get_layer_thumbnail_path,
                             process_client.MAP_TYPE: map_thumbnail.get_map_thumbnail_path}

    exp_thumbnail = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('thumbnail')
    if exp_thumbnail:
        with app.app_context():
            thumbnail_path = thumbnail_path_method[publ_type](workspace, publication)
        diffs = test_util.compare_images(exp_thumbnail, thumbnail_path)
        assert diffs < 1000
