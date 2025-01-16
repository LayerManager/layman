import pytest

import crs as crs_def
from layman import app
from test_tools import assert_util
from . import bbox as bbox_util


@pytest.mark.parametrize('bbox, expected_result', [
    ((None, None, None, None, ), True),
    ((1, None, None, None,), False),
    ((None, 1, None, None,), False),
    ((None, None, 1, None,), False),
    ((None, None, None, 1,), False),
    ((2, 10, 3, 12,), False),
])
def test_is_empty(bbox, expected_result):
    assert bbox_util.is_empty(bbox) == expected_result


@pytest.mark.parametrize('bbox, expected_result', [
    ((None, None, None, None, ), True),
    ((1, 2, 3, 4, ), True),
    ((1, 2, 1, 2, ), True),
    ((1, None, None, None,), False),
    ((3, 1, 2, 4,), False),
    ((2, 2, 3, -4,), False),
])
def test_is_valid(bbox, expected_result):
    assert bbox_util.is_valid(bbox) == expected_result


@pytest.mark.parametrize('bbox1, bbox2, expected_result', [
    ((1, 1, 4, 4, ), (2, 2, 3, 3, ), True),
    ((1, 1, 4, 4, ), (1, 1, 4, 4, ), True),
    ((1, 1, 4, 4, ), (1, 1, 4, 5, ), False),
    ((-4, -4, -1, -1, ), (-3, -3, -2, -2, ), True),
    ((1, 1, 4, 4, ), (None, None, None, None, ), False),
    ((None, None, None, None, ), (1, 1, 4, 4, ), False),
])
def test_contains_bbox(bbox1, bbox2, expected_result):
    assert bbox_util.contains_bbox(bbox1, bbox2) == expected_result


@pytest.mark.parametrize('bbox1, bbox2, expected_result', [
    ((1, 1, 4, 4, ), (2, 2, 3, 3, ), True),
    ((1, 1, 4, 4, ), (1, 1, 4, 4, ), True),
    ((1, 1, 4, 4, ), (1, 1, 4, 5, ), True),
    ((1, 1, 4, 4, ), (4, 4, 5, 5, ), True),
    ((1, 1, 4, 4, ), (5, 5, 6, 6, ), False),
    ((1, 1, 4, 4, ), (None, None, None, None, ), False),
    ((None, None, None, None, ), (1, 1, 4, 4, ), False),
])
def test_intersects_bbox(bbox1, bbox2, expected_result):
    assert bbox_util.intersects(bbox1, bbox2) == expected_result


@pytest.mark.parametrize('bbox, expected_result', [
    ((1, 1, 4, 4, ), True),
    ((1, 1, 1, 3, ), False),
    ((1, 1, 4, 1, ), False),
    ((1, 1, 1, 1, ), False),
    ((None, None, None, None, ), False),
])
def test_has_area(bbox, expected_result):
    assert bbox_util.has_area(bbox) == expected_result


@pytest.mark.parametrize('bbox, no_area_padding, expected_result', [
    ((1, 1, 4, 4, ), 10, (1, 1, 4, 4, )),
    ((1, 1, 1, 3, ), 10, (-9, 1, 11, 3)),
    ((1, 1, 4, 1, ), 10, (1, -9, 4, 11)),
    ((1, 1, 1, 1, ), 10, (-9, -9, 11, 11)),
])
def test_ensure_bbox_with_area(bbox, no_area_padding, expected_result):
    assert bbox_util.ensure_bbox_with_area(bbox, no_area_padding) == expected_result


@pytest.mark.parametrize('bbox, crs, expected_result', [
    ((1, 1, 4, 4,), crs_def.EPSG_4326, (1, 1, 4, 4,)),
    ((1, 2, 1, 2,), crs_def.EPSG_4326, (0.99999, 1.99999, 1.00001, 2.00001)),
    ((1, 2, 1, 2,), crs_def.EPSG_3857, (-9, -8, 11, 12)),
    ((None, None, None, None,), crs_def.EPSG_4326, (
        -180,
        -90,
        180,
        90,
    )),
    ((None, None, None, None,), crs_def.EPSG_3857, (
        -20026376.39,
        -20048966.10,
        20026376.39,
        20048966.10,
    )),
])
def test_get_bbox_to_publish(bbox, crs, expected_result):
    assert bbox_util.get_bbox_to_publish(bbox, crs) == expected_result


@pytest.mark.parametrize('bbox, crs_from, crs_to, expected_bbox', [
    (
        crs_def.CRSDefinitions[crs_def.EPSG_4326].default_bbox,
        crs_def.EPSG_4326,
        crs_def.EPSG_3857,
        crs_def.CRSDefinitions[crs_def.EPSG_3857].default_bbox,
    ),
    (
        [180, 90, 180, 90],
        crs_def.EPSG_4326,
        crs_def.EPSG_3857,
        [20026376.39, 20048966.1, 20026376.39, 20048966.1],
    ),
    (
        [-180, -90, -180, -90],
        crs_def.EPSG_4326,
        crs_def.EPSG_3857,
        [-20026376.39, -20048966.1, -20026376.39, -20048966.1],
    ),
    (
        [-598214.7290553625207394, -1160319.8064114262815565, -598200.9321668159682304, -1160307.4425631782505661],
        crs_def.EPSG_5514,
        crs_def.EPSG_3857,
        [1848640.4769060146, 6308683.577507495, 1848663.461145939, 6308704.681240051],
    ),
])
def test_transform(bbox, crs_from, crs_to, expected_bbox):
    with app.app_context():
        transformed_bbox = bbox_util.transform(bbox, crs_from, crs_to)
    assert_util.assert_same_bboxes(transformed_bbox, expected_bbox, 0.1)
