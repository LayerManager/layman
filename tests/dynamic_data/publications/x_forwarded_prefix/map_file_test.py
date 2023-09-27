import json
import logging
import os
import pytest

import jsonpath_ng as jp
from test_tools import process_client
from tests import Publication
from tests.dynamic_data import base_test

logger = logging.getLogger(__name__)

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

WORKSPACE = 'map_file_workspace'

LAYER_HRANICE = Publication(WORKSPACE, process_client.LAYER_TYPE, 'hranice')
MAP = Publication(WORKSPACE, process_client.MAP_TYPE, 'map_hranice')
MAP_FILE_PATH = os.path.join(DIRECTORY, 'internal_wms_and_wfs.json')


def _find_single_value_in_json(json_path_str, json_obj):
    json_path_expr = jp.parse(json_path_str)
    values = [m.value for m in json_path_expr.find(json_obj)]
    assert len(values) == 1, f"key={json_path_str}"
    return values[0]


@pytest.mark.usefixtures('oauth2_provider_mock')
class TestPublication(base_test.TestSingleRestPublication):
    workspace = WORKSPACE
    publication_type = process_client.MAP_TYPE

    rest_parametrization = []

    def before_class(self):
        self.post_publication(MAP, args={
            'file_paths': [MAP_FILE_PATH],
        }, scope='class')

    @pytest.mark.parametrize('headers, exp_url_prefix', [
        pytest.param({}, 'http://localhost:8000', id='no-client-proxy-prefix'),
        pytest.param({'X-Forwarded-Prefix': ''}, 'http://localhost:8000', id='empty-client-proxy-prefix'),
        pytest.param({'X-Forwarded-Prefix': '/some-client-proxy'}, 'http://localhost:8000/some-client-proxy',
                     id='some-client-proxy-prefix'),
        pytest.param({'X-Forwarded-Proto': 'https',
                      'X-Forwarded-Host': 'enjoychallenge.tech',
                      'X-Forwarded-Prefix': '/some-client-proxy',
                      }, 'https://enjoychallenge.tech/some-client-proxy', id='full-client-proxy-prefix'),
    ])
    def test_x_forwarded_prefix(self, headers, exp_url_prefix):
        map = MAP
        resp = process_client.get_workspace_map_file(map.type, map.workspace, map.name, headers=headers)

        exp_adjusted_urls = [
            ('$.layers[1].url', '/geoserver/ows'),
            ('$.layers[1].legends[0]', '/geoserver/ows?service=WMS&version=1.3.0&request=GetLegendGraphic&format=image%2Fpng&width=20&height=20&layer=map_file_workspace_wms%3Ahranice'),
            ('$.layers[2].url', '/geoserver/map_file_workspace_wms/ows'),
            ('$.layers[2].style', '/rest/workspaces/map_file_workspace/layers/mista/style'),
            ('$.layers[3].protocol.url', '/geoserver/map_file_workspace_workspace/wfs'),
        ]

        for json_path_str, exp_url_postfix in exp_adjusted_urls:
            found_value = _find_single_value_in_json(json_path_str, resp)
            exp_value = f"{exp_url_prefix}{exp_url_postfix}"
            assert found_value == exp_value, f"key={json_path_str}"

        with open(MAP_FILE_PATH, encoding='utf-8') as file:
            orig_json = json.load(file)

        exp_unchanged_urls = [
            '$.layers[0].url',
            '$.layers[0].legends[0]',
            '$.layers[1].legends[1]',
            '$.layers[1].style',
            '$.layers[3].style',
            '$.layers[4].url',
            '$.layers[4].style',
        ]
        for json_path_str in exp_unchanged_urls:
            exp_url = _find_single_value_in_json(json_path_str, orig_json)
            found_value = _find_single_value_in_json(json_path_str, resp)
            assert found_value == exp_url, f"key={json_path_str}"
