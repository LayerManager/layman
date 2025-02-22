from copy import deepcopy
import os
import pytest

from test_tools import cleanup
from tests.asserts.final import publication as publ_asserts
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test, base_test_classes
from ... import Publication4Test, EnumTestTypes, EnumTestKeys

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

TEST_CASES = {
    'starts_with_number': {'name': '0125_name',
                           EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL},
    'only_numbers': {'name': '0125'},
    '210_chars': {'name': 'a' * 210},
}

pytest_generate_tests = base_test.pytest_generate_tests


def generate_test_cases():
    test_cases = []
    for key, test_case_params in TEST_CASES.items():
        all_params = deepcopy(test_case_params)
        test_type = all_params.pop(EnumTestKeys.TYPE, EnumTestTypes.MANDATORY)

        test_case = base_test.TestCaseType(publication=lambda publ_def, cls, params: Publication4Test(cls.workspace,
                                                                                                      publ_def.type,
                                                                                                      params['name']),
                                           key=key,
                                           params=all_params,
                                           type=test_type,
                                           )
        test_cases.append(test_case)
    return test_cases


class TestPublication(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_publication_name'
    test_cases = generate_test_cases()
    publication_type = None

    rest_parametrization = [
        base_test.PublicationByUsedServers,
    ]

    external_tables_to_create = base_test_classes.EXTERNAL_TABLE_FOR_LAYERS_BY_USED_SERVERS

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
    def test_publication_name(publication, rest_method, rest_args, parametrization):
        """Parametrized using pytest_generate_tests"""
        publ_def = parametrization.publication_definition
        rest_method.fn(publication, args=rest_args)
        assert_util.is_publication_valid_and_complete(publication)
        publ_asserts.internal.correct_values_in_detail(publication.workspace, publication.type, publication.name,
                                                       **publ_def.info_values)
        if publ_def.thumbnail:
            publ_asserts.internal.thumbnail_equals(publication.workspace, publication.type, publication.name,
                                                   exp_thumbnail=publ_def.thumbnail)
