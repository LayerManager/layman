import pytest
from layman import app, util as layman_util, settings
from layman.layer.filesystem import gdal
from test_tools import assert_util
from ... import single_static_publication as data
from ..data import ensure_publication


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
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
