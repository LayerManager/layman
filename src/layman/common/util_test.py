import pytest
from . import util


@pytest.mark.parametrize('bbox, expected_result', [
    ((None, None, None, None, ), True),
    ((1, None, None, None,), False),
    ((None, 1, None, None,), False),
    ((None, None, 1, None,), False),
    ((None, None, None, 1,), False),
    ((2, 10, 3, 12,), False),
])
def test_bbox_is_empty(bbox, expected_result):
    assert util.bbox_is_empty(bbox) == expected_result
