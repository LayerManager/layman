import os
import pytest
import requests

from layman import app, settings
from test_tools import process_client
from tests import Publication4Test, EnumTestTypes
from tests.asserts.final.publication import internal as assert_internal
from tests.dynamic_data import base_test
from layman.util import get_publication_uuid

pytest_generate_tests = base_test.pytest_generate_tests

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

USER = 'test_uuid_map_thumbnail'
WORKSPACE = 'test_uuid_map_thumbnail_ws' 
MAP = Publication4Test(WORKSPACE, process_client.MAP_TYPE, 'map_test')


@pytest.mark.timeout(60)
@pytest.mark.usefixtures('oauth2_provider_mock')
class TestPublication(base_test.TestSingleRestPublication):
    workspace = WORKSPACE
    publication_type = process_client.MAP_TYPE

    usernames_to_reserve = [USER]

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
            'actor_name': USER,
        }, scope='class')         
   

    def test_publication(self):  
        with app.app_context():
            map_uuid = get_publication_uuid(MAP.workspace, MAP.type, MAP.name)
            response = requests.get(
                f"http://{settings.LAYMAN_SERVER_NAME}/rest/maps/{map_uuid}/thumbnail"
            )
        if response.status_code != 200:
            print(f"Error response: {response.status_code}")
            print(f"Response content: {response.text}")
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'image/png'    
    
        exp_thumbnail = os.path.join(DIRECTORY, "empty_map_thumbnail.png")
        assert_internal.thumbnail_equals(MAP.workspace, MAP.type, MAP.name, exp_thumbnail, max_diffs=0)
