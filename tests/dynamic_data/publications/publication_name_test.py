import copy
import os
import pytest

from test_tools import process_client, cleanup
from tests.asserts.final import publication as publ_asserts
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test
from tests.dynamic_data.publications import common_publications
from ... import Publication, TestTypes, TestKeys, PublicationValues

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

TEST_CASES = {
    'starts_with_number': {'name': '0125_name'},
    'only_numbers': {'name': '0125'},
}

TEST_CASE_PARAMETRIZATION = {
    'vector_sld_layer': common_publications.LAYER_VECTOR_SLD,
    'vector_qml_layer': common_publications.LAYER_VECTOR_QML,
    'raster_layer': common_publications.LAYER_RASTER,
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
            for parametrization_key, publication_definition in TEST_CASE_PARAMETRIZATION.items():
                publ_name = params['name']
                publication = Publication(cls.workspace, cls.publication_type, publ_name)
                rest_method = getattr(cls, method_function_name)
                testcase_id = f'{publ_name}:{parametrization_key}_{method_name}'

                post_definition = copy.deepcopy(params)
                post_definition.update(publication_definition.definition)
                post_definition.pop('name', None)

                test_case_definition = PublicationValues(
                    type=publication_definition.type,
                    definition=post_definition,
                    info_values=publication_definition.info_values,
                    thumbnail=publication_definition.thumbnail,
                )

                argvalues.append([
                    publication,
                    key,
                    test_case_definition,
                    rest_method,
                    (publication, method_name),
                ])
                ids.append(testcase_id)
    publ_type_name = cls.publication_type.split('.')[-1]
    metafunc.parametrize(
        argnames=f'{publ_type_name}, key, publication_definition, rest_method, post_before_patch',
        argvalues=argvalues,
        ids=ids,
        indirect=['post_before_patch'],
    )


class TestPublication(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_publication_name'
    test_cases = TEST_CASES
    default_test_type = TestTypes.MANDATORY
    publication_type = process_client.LAYER_TYPE

    rest_parametrization = {
        'method': {
            'post_publication': 'post',
        },
    }

    @pytest.fixture(scope='class', autouse=True)
    def class_cleanup(self, request):
        yield
        cleanup.cleanup_publications(request, self.publications_to_cleanup_on_class_end, force=True)
        self.publications_to_cleanup_on_class_end.clear()

    @pytest.fixture(scope='function', autouse=True)
    def function_cleanup(self, request):
        yield
        cleanup.cleanup_publications(request, self.publications_to_cleanup_on_function_end, force=True)
        self.publications_to_cleanup_on_function_end.clear()

    # pylint: disable=unused-argument
    @staticmethod
    def test_publication_name(layer, key, publication_definition, rest_method):
        """Parametrized using pytest_generate_tests"""
        rest_method(layer, params=publication_definition.definition)
        assert_util.is_publication_valid_and_complete(layer)
        publ_asserts.internal.correct_values_in_detail(layer.workspace, layer.type, layer.name,
                                                       **publication_definition.info_values)
        publ_asserts.internal.thumbnail_equals(layer.workspace, layer.type, layer.name,
                                               exp_thumbnail=publication_definition.thumbnail)
