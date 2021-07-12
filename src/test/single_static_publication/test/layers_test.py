import pytest
from layman import app, util as layman_util, settings
from layman.layer.filesystem import gdal, thumbnail as fs_thumbnail
from test_tools import util as test_util, assert_util
from ... import single_static_publication as data
from ..data import ensure_publication


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_LAYERS)
@pytest.mark.usefixtures('ensure_layman')
def test_bbox(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    with app.app_context():
        info = layman_util.get_publication_info(workspace, publ_type, publication, context={'keys': ['bounding_box']})

    exp_bbox = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA]['bbox']

    info_bbox = info['bounding_box']
    assert_util.assert_same_bboxes(info_bbox, exp_bbox, 0.01)

    file_type = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('file_type')
    if file_type == settings.FILE_TYPE_RASTER:
        bbox = gdal.get_bbox(workspace, publication)
        assert_util.assert_same_bboxes(bbox, exp_bbox, 0.01)


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
