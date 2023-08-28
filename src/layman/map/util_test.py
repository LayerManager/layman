import json
import pytest
from . import util as map_util


@pytest.mark.parametrize('json_path, exp_result', [
    ('sample/layman.map/internal_url.json', {
        ('testuser1', 'hranice', 1),
        ('testuser1', 'mista', 2),
    }),
    ('sample/layman.map/full.json', set()),
])
def test_get_layers_from_json(json_path, exp_result):
    with open(json_path, 'r', encoding="utf-8") as map_file:
        map_json = json.load(map_file)
    result = map_util.get_layers_from_json(map_json)
    assert result == exp_result
