import os

import tests
from test_tools import process_client
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

TEST_CASES = {
    'starts_with_number': {'name': '0125_name'},
}


pytest_generate_tests = base_test.pytest_generate_tests


class TestPublication(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_publication_name'
    test_cases = TEST_CASES
    default_test_type = tests.TestTypes.MANDATORY
    publication_type = process_client.LAYER_TYPE

    rest_parametrization = {
        'method': {
            'post_publication': 'post',
        },
    }

    # pylint: disable=unused-argument
    @staticmethod
    def test_publication_name(layer, key, params, rest_method):
        """Parametrized using pytest_generate_tests"""
        rest_method(layer, params=params)
        assert_util.is_publication_valid_and_complete(layer)
