import os
import pytest
import requests

from layman import app, settings
from layman.util import get_publication_uuid
from test_tools import process_client
from tests import Publication4Test, EnumTestTypes
from tests.dynamic_data import base_test

pytest_generate_tests = base_test.pytest_generate_tests

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

WORKSPACE = 'test_uuid_map_thumbnail_ws'
MAP = Publication4Test(WORKSPACE, process_client.MAP_TYPE, 'map_test')
LAYER = Publication4Test(WORKSPACE, process_client.LAYER_TYPE, 'layer_test')


@pytest.mark.timeout(60)
@pytest.mark.usefixtures('oauth2_provider_mock')
class TestPublication(base_test.TestSingleRestPublication):
    workspace = WORKSPACE
    publication_type = process_client.MAP_TYPE

    test_cases = [base_test.TestCaseType(
        key='main',
        publication=MAP,
        type=EnumTestTypes.MANDATORY,
    )]

    def before_class(self):
        self.post_publication(MAP, args={
            'file_paths': [os.path.join(DIRECTORY, 'map.json')],
            'access_rights': {
                'read': 'EVERYONE',
                'write': 'EVERYONE',
            },
        }, scope='class')
        self.post_publication(LAYER, args={
            'access_rights': {
                'read': 'EVERYONE',
                'write': 'EVERYONE',
            },
        }, scope='class')

    def test_map_uuid(self):
        with app.app_context():
            map_uuid = get_publication_uuid(MAP.workspace, MAP.type, MAP.name)
            response = requests.get(
                f"http://{settings.LAYMAN_SERVER_NAME}/rest/maps/{map_uuid}/thumbnail"
            )
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'image/png'

    def test_layer_uuid_in_map_endpoint(self):
        with app.app_context():
            layer_uuid = get_publication_uuid(LAYER.workspace, LAYER.type, LAYER.name)
            response = requests.get(
                f"http://{settings.LAYMAN_SERVER_NAME}/rest/maps/{layer_uuid}/thumbnail"
            )
        assert response.status_code == 404
        response_json = response.json()
        assert response_json['code'] == 26
        assert response_json['detail']['uuid'] == layer_uuid

    def test_layer_uuid(self):
        with app.app_context():
            layer_uuid = get_publication_uuid(LAYER.workspace, LAYER.type, LAYER.name)
            response = requests.get(
                f"http://{settings.LAYMAN_SERVER_NAME}/rest/layers/{layer_uuid}/thumbnail"
            )
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'image/png'

    def test_map_uuid_in_layer_endpoint(self):
        with app.app_context():
            map_uuid = get_publication_uuid(MAP.workspace, MAP.type, MAP.name)
            response = requests.get(
                f"http://{settings.LAYMAN_SERVER_NAME}/rest/layers/{map_uuid}/thumbnail"
            )
        assert response.status_code == 404
        response_json = response.json()
        assert response_json['code'] == 15
        assert response_json['detail']['uuid'] == map_uuid
