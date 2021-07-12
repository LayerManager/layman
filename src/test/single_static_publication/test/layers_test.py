import pytest
from layman import app
from layman.layer.filesystem import thumbnail as fs_thumbnail
from test_tools import util as test_util
from ... import single_static_publication as data
from ..data import ensure_publication


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_LAYERS)
@pytest.mark.usefixtures('ensure_layman')
def test_thumbnail(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    exp_thumbnail = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('thumbnail')
    if exp_thumbnail:
        with app.app_context():
            thumbnail_path = fs_thumbnail.get_layer_thumbnail_path(workspace, publication)
        diffs = test_util.compare_images(exp_thumbnail, thumbnail_path)
        assert diffs < 1000
