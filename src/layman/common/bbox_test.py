import pytest

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
