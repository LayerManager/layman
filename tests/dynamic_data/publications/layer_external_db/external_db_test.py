import os
from urllib.parse import quote
import pytest

from db import util as db_util
from test_tools import process_client, external_db
from tests import EnumTestTypes, Publication
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

TEST_CASES = {
    'all': {
        'input_file_name': 'all',
        'table_name': 'all',
        'exp_geometry_type': 'GEOMETRY',
    },
    'geometrycollection_mixed_case_table_name': {
        'input_file_name': 'geometrycollection',
        'table_name': 'MyGeometryCollection',
        'exp_geometry_type': 'GEOMETRYCOLLECTION',
    },
    'linestring_dangerous_table_name': {
        'input_file_name': 'linestring',
        'table_name': '; DROP TABLE "public"."abc"; SELECT \'& Žlu-ťouč-ký\'',
        'exp_geometry_type': 'LINESTRING',
    },
    'multilinestring': {
        'input_file_name': 'multilinestring',
        'table_name': 'multilinestring',
        'exp_geometry_type': 'MULTILINESTRING',
    },
    'multipoint': {
        'input_file_name': 'multipoint',
        'table_name': 'multipoint',
        'exp_geometry_type': 'MULTIPOINT',
    },
    'multipolygon': {
        'input_file_name': 'multipolygon',
        'table_name': 'multipolygon',
        'exp_geometry_type': 'MULTIPOLYGON',
    },
    'point': {
        'input_file_name': 'point',
        'table_name': 'point',
        'exp_geometry_type': 'POINT',
    },
    'polygon': {
        'input_file_name': 'polygon',
        'table_name': 'polygon',
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
                                             'db_connection': f"{external_db.URI_STR}?schema=public&table={quote(value['table_name'])}&geo_column=wkb_geometry",
                                         },
                                         params=value,
                                         ) for key, value in TEST_CASES.items()]

    @staticmethod
    def test_layer(layer: Publication, rest_method, rest_args, params):
        """Parametrized using pytest_generate_tests"""
        file_path = f"sample/data/geometry-types/{params['input_file_name']}.geojson"
        table = params['table_name']
        external_db.import_table(file_path, table=table)
        conn_cur = db_util.create_connection_cursor(external_db.URI_STR)
        query = f'''select type from geometry_columns where f_table_schema = %s and f_table_name = %s and f_geometry_column = %s'''
        result = db_util.run_query(query, ('public', table, 'wkb_geometry'), conn_cur=conn_cur)
        assert result[0][0] == params['exp_geometry_type']

        rest_method(layer, args=rest_args)

        external_db.drop_table('public', table)
