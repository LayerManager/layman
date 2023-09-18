import logging
import os
import pytest

import jsonpath_ng as jp
from layman import settings
from test_tools import process_client
from tests import Publication
from tests.dynamic_data import base_test

logger = logging.getLogger(__name__)

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

WORKSPACE = 'map_file_workspace'

LAYER_HRANICE = Publication(WORKSPACE, process_client.LAYER_TYPE, 'hranice')
MAP = Publication(WORKSPACE, process_client.MAP_TYPE, 'map_hranice')


@pytest.mark.usefixtures('oauth2_provider_mock')
class TestPublication(base_test.TestSingleRestPublication):
    workspace = WORKSPACE
    publication_type = process_client.MAP_TYPE

    rest_parametrization = []

    def before_class(self):
        self.post_publication(MAP, args={
            'file_paths': [os.path.join(DIRECTORY, 'internal_wms_and_wfs.json')],
        }, scope='class')

    @pytest.mark.parametrize('headers', [
        pytest.param({}, id='no-client-proxy'),
        pytest.param({'X-Forwarded-Prefix': ''}, id='empty-client-proxy'),
        pytest.param({'X-Forwarded-Prefix': '/some-client-proxy'}, id='some-client-proxy'),
    ])
    def test_x_forwarded_prefix(self, headers):
        map = MAP
        resp = process_client.get_workspace_map_file(map.type, map.workspace, map.name, headers=headers)

        exp_adjusted_urls = [
            ('$.layers[1].url', '/geoserver/ows'),
            ('$.layers[2].url', '/geoserver/map_file_workspace_wms/ows'),
            ('$.layers[3].protocol.url', '/geoserver/map_file_workspace_workspace/wfs'),
        ]

        x_forwarded_prefix = headers.get('X-Forwarded-Prefix', '')
        for json_path_str, exp_url_postfix in exp_adjusted_urls:
            json_path_expr = jp.parse(json_path_str)
            values = [m.value for m in json_path_expr.find(resp)]
            assert len(values) == 1, f"key={json_path_str}"
            found_value = values[0]
            exp_value = f"http://{settings.LAYMAN_PROXY_SERVER_NAME}{x_forwarded_prefix}{exp_url_postfix}"
            assert found_value == exp_value, f"key={json_path_str}"
