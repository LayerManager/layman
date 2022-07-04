import copy
import os
import pytest

from test_tools import cleanup
from tests.asserts.final import publication as publ_asserts
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test
from tests.dynamic_data.publications import common_publications
from ... import Publication, TestTypes, TestKeys, PublicationValues

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

TEST_CASES = {
    'starts_with_number': {'name': '0125_name'},
    'only_numbers': {'name': '0125'},
    '210_chars': {'name': 'a' * 210},
}

pytest_generate_tests = base_test.pytest_generate_tests

PUBLICATION_TYPES = {
    'vector_sld_layer': common_publications.LAYER_VECTOR_SLD,
    'vector_qml_layer': common_publications.LAYER_VECTOR_QML,
    'raster_layer': common_publications.LAYER_RASTER,
    'map': common_publications.MAP_EMPTY,
}


def parametrize_test(workspace, input_test_cases, publication_types):
    test_cases = []
    for key, params in input_test_cases.items():
        for parametrization_key, publication_definition in publication_types.items():
            name = params['name']
            test_case_id = f'{name}:{parametrization_key}_post'

            post_definition = copy.deepcopy(params)
            post_definition.update(publication_definition.definition)
            post_definition.pop('name', None)

            test_case_definition = PublicationValues(
                type=publication_definition.type,
                definition=post_definition,
                info_values=publication_definition.info_values,
                thumbnail=publication_definition.thumbnail,
            )

            test_case = base_test.TestCaseType(id=test_case_id,
                                               publication=Publication(workspace, publication_definition.type, name),
                                               key=key,
                                               method=None,
                                               params=test_case_definition,
                                               type=params.get(TestKeys.TYPE, TestTypes.MANDATORY)
                                               )
            test_cases.append(test_case)
    return test_cases


class TestPublication(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_publication_name'
    test_cases = parametrize_test('dynamic_test_publication_name', TEST_CASES, PUBLICATION_TYPES)
    default_test_type = TestTypes.MANDATORY
    publication_type = None

    rest_parametrization = {
        'method': [
            base_test.RestMethodType('post_publication', 'post'),
        ],
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
    def test_publication_name(publication, key, params, rest_method):
        """Parametrized using pytest_generate_tests"""
        rest_method(publication, params=params.definition)
        assert_util.is_publication_valid_and_complete(publication)
        publ_asserts.internal.correct_values_in_detail(publication.workspace, publication.type, publication.name,
                                                       **params.info_values)
        if params.thumbnail:
            publ_asserts.internal.thumbnail_equals(publication.workspace, publication.type, publication.name,
                                                   exp_thumbnail=params.thumbnail)
