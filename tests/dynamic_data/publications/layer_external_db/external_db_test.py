import os
import pytest

from test_tools import process_client, external_db
from tests import EnumTestTypes, Publication, EnumTestKeys
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

TEST_CASES = {
    'external_vector_sld': {
        'rest_args': {
            'db_connection': 'postgresql://docker:docker@postgresql:5432/external_test_db?table=schema.table_name&geo_column=geo_wkb_column',
        },
    },
}


class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_layer_external_db'

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = []

    test_cases = [base_test.TestCaseType(key=key,
                                         type=value.get(EnumTestKeys.TYPE, EnumTestTypes.MANDATORY),
                                         params=value,
                                         rest_args=value['rest_args'],
                                         marks=[pytest.mark.xfail(reason="Not yet implemented.")]
                                         if value.get('xfail') else []
                                         ) for key, value in TEST_CASES.items()]

    @staticmethod
    def test_style_xml(layer: Publication, rest_method, rest_args):
        """Parametrized using pytest_generate_tests"""
        external_db.ensure_db()
        external_db.ensure_table('schema', 'table_name', 'geo_wkb_column')
        rest_method(layer, args=rest_args)
