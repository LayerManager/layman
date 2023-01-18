import os
import pytest

from db import util as db_util
from test_tools import process_client, external_db
from tests import EnumTestTypes, Publication
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

TEST_CASES = {
    'all': {
        'exp_geometry_type': 'GEOMETRY',
    },
    'geometrycollection': {
        'exp_geometry_type': 'GEOMETRYCOLLECTION',
    },
    'linestring': {
        'exp_geometry_type': 'LINESTRING',
    },
    'multilinestring': {
        'exp_geometry_type': 'MULTILINESTRING',
    },
    'multipoint': {
        'exp_geometry_type': 'MULTIPOINT',
    },
    'multipolygon': {
        'exp_geometry_type': 'MULTIPOLYGON',
    },
    'point': {
        'exp_geometry_type': 'POINT',
    },
    'polygon': {
        'exp_geometry_type': 'POLYGON',
    },
}


@pytest.mark.usefixtures('ensure_external_db')
class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_layer_external_db_geometry_type'

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = []

    test_cases = [base_test.TestCaseType(key=key,
                                         type=EnumTestTypes.MANDATORY,
                                         rest_args={
                                             'db_connection': f"{external_db.URI_STR}?table=public.{key}&geo_column=wkb_geometry",
                                         },
                                         params=value,
                                         ) for key, value in TEST_CASES.items()]

    @staticmethod
    def test_layer(layer: Publication, key, rest_method, rest_args, params):
        """Parametrized using pytest_generate_tests"""
        file_path = f"sample/data/geometry-types/{key}.geojson"

        external_db.import_table(file_path, table=key)
        conn_cur = db_util.create_connection_cursor(external_db.URI_STR)
        query = f'''select type from geometry_columns where f_table_schema = %s and f_table_name = %s and f_geometry_column = %s'''
        result = db_util.run_query(query, ('public', key, 'wkb_geometry'), conn_cur=conn_cur)
        assert result[0][0] == params['exp_geometry_type']

        rest_method(layer, args=rest_args)

        external_db.drop_table('public', key)
