import os
import pytest

from test_tools import process_client
from tests import EnumTestTypes, Publication
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

TEST_CASES = {
    'qml_only_with_point_labels': {
        'rest_args': {
            'file_paths': [
                os.path.join(DIRECTORY, 'BODOVE_POLE_T.cpg'),
                os.path.join(DIRECTORY, 'BODOVE_POLE_T.dbf'),
                os.path.join(DIRECTORY, 'BODOVE_POLE_T.prj'),
                os.path.join(DIRECTORY, 'BODOVE_POLE_T.shp'),
                os.path.join(DIRECTORY, 'BODOVE_POLE_T.shx'),
            ],
            'style_file': 'sample/style/labels_without_symbols/BODOVE_POLE_T.qml',
        },
    },
    'points_clustering': {
        'rest_args': {
            'file_paths': [
                os.path.join(DIRECTORY, 'cluster.geojson'),
            ],
            'style_file': 'sample/style//cluster.qml',
        },
    },
}


class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_layer_style'

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = [
    ]

    test_cases = [base_test.TestCaseType(key=key,
                                         type=EnumTestTypes.OPTIONAL,
                                         rest_args=value.get('rest_args'),
                                         params=value,
                                         marks=[pytest.mark.xfail(reason="Not yet implemented.")]
                                         if value.get('xfail') else []
                                         ) for key, value in TEST_CASES.items()]

    @staticmethod
    def test_qml_style(layer: Publication, rest_args, rest_method):
        """Parametrized using pytest_generate_tests"""
        rest_method.fn(layer, args=rest_args)

        assert_util.is_publication_valid_and_complete(layer)
