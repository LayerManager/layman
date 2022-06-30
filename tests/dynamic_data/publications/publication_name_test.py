import copy
import os

import tests
from test_tools import process_client
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test
from ... import Publication, TestTypes, TestKeys


DIRECTORY = os.path.dirname(os.path.abspath(__file__))

TEST_CASES = {
    'starts_with_number': {'name': '0125_name'},
}


def pytest_generate_tests(metafunc):
    # used for parametrizing subclasses of TestSingleRestPublication, called once per each test function
    # https://docs.pytest.org/en/6.2.x/parametrize.html#pytest-generate-tests
    test_type_str = os.getenv(TestKeys.TYPE.value, TestTypes.MANDATORY.value)
    test_type = TestTypes(test_type_str)
    cls = metafunc.cls
    rest_methods = cls.rest_parametrization['method']
    argvalues = []
    ids = []

    test_cases_for_type = {key: params for key, params in cls.test_cases.items() if
                           test_type == TestTypes.OPTIONAL or params.get(TestKeys.TYPE, cls.default_test_type) == TestTypes.MANDATORY}
    for key, params in test_cases_for_type.items():
        for method_function_name, method_name in rest_methods.items():
            publ_name = cls.key_to_publication_base_name(key) + f"_{method_name}"
            publication = Publication(cls.workspace, cls.publication_type, publ_name)
            rest_method = getattr(cls, method_function_name)
            argvalues.append([
                publication,
                key,
                copy.deepcopy(params),
                rest_method,
                (publication, method_name),
            ])
            ids.append(publ_name)
    publ_type_name = cls.publication_type.split('.')[-1]
    metafunc.parametrize(
        argnames=f'{publ_type_name}, key, params, rest_method, post_before_patch',
        argvalues=argvalues,
        ids=ids,
        indirect=['post_before_patch'],
    )


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
