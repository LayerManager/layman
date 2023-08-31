from layman import settings
from test_tools import process_client
from tests import EnumTestTypes
from tests.dynamic_data import base_test

pytest_generate_tests = base_test.pytest_generate_tests


class TestPostPublication(base_test.TestSingleRestPublication):
    workspace = 'x_forwarded_prefix_post_workspace'
    rest_parametrization = []

    test_cases = [base_test.TestCaseType(key='post_layer',
                                         publication_type=process_client.LAYER_TYPE,
                                         type=EnumTestTypes.MANDATORY,
                                         )]

    @staticmethod
    def test_publication(publication, rest_method):
        proxy_prefix = '/layman-proxy'
        response = rest_method(publication, args={'headers': {'X-Forwarded-Prefix': proxy_prefix}})
        assert response['url'] == f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/rest/workspaces/{publication.workspace}/layers/{publication.name}'
