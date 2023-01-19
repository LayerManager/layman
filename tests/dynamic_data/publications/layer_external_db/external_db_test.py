import os
from urllib.parse import quote
import pytest

from db import util as db_util
from layman import settings, app
from test_tools import process_client, external_db
from tests import EnumTestTypes, Publication
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

DANGEROUS_NAME = '; DROP TABLE "public"."abc"; SELECT \'& Žlu-ťouč-ký\''

TEST_CASES = {
    'all': {
        'input_file_name': 'all',
        'schema_name': 'public',
        'table_name': 'all',
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'GEOMETRY',
    },
    'geometrycollection_mixed_case_table_name': {
        'input_file_name': 'geometrycollection',
        'schema_name': 'public',
        'table_name': 'MyGeometryCollection',
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'GEOMETRYCOLLECTION',
    },
    'linestring_dangerous_table_name': {
        'input_file_name': 'linestring',
        'schema_name': 'public',
        'table_name': DANGEROUS_NAME,
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'LINESTRING',
    },
    'multilinestring_dangerous_schema_name': {
        'input_file_name': 'multilinestring',
        'schema_name': DANGEROUS_NAME,
        'table_name': 'multilinestring',
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'MULTILINESTRING',
    },
    'multipoint_dangerous_geo_column_name': {
        'input_file_name': 'multipoint',
        'schema_name': 'public',
        'table_name': 'multipoint',
        'geo_column_name': DANGEROUS_NAME,
        'exp_geometry_type': 'MULTIPOINT',
    },
    'multipolygon': {
        'input_file_name': 'multipolygon',
        'schema_name': 'public',
        'table_name': 'multipolygon',
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'MULTIPOLYGON',
    },
    'point': {
        'input_file_name': 'point',
        'schema_name': 'public',
        'table_name': 'point',
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'POINT',
    },
    'polygon': {
        'input_file_name': 'polygon',
        'schema_name': 'public',
        'table_name': 'polygon',
        'geo_column_name': 'wkb_geometry',
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
                                             'db_connection': f"{external_db.URI_STR}"
                                                              f"?schema={quote(value['schema_name'])}"
                                                              f"&table={quote(value['table_name'])}"
                                                              f"&geo_column={quote(value['geo_column_name'])}",
                                         },
                                         params=value,
                                         ) for key, value in TEST_CASES.items()]

    @staticmethod
    def test_layer(layer: Publication, rest_method, rest_args, params):
        """Parametrized using pytest_generate_tests"""
        file_path = f"sample/data/geometry-types/{params['input_file_name']}.geojson"
        schema = params['schema_name']
        table = params['table_name']
        geo_column = params['geo_column_name']

        external_db.import_table(file_path, table=table, schema=schema, geo_column=geo_column)
        conn_cur = db_util.create_connection_cursor(external_db.URI_STR)
        query = f'''select type from geometry_columns where f_table_schema = %s and f_table_name = %s and f_geometry_column = %s'''
        result = db_util.run_query(query, (schema, table, geo_column), conn_cur=conn_cur)
        assert result[0][0] == params['exp_geometry_type']

        rest_method(layer, args=rest_args)

        query = f'''select p.external_table_uri
            from {settings.LAYMAN_PRIME_SCHEMA}.publications p left join
             {settings.LAYMAN_PRIME_SCHEMA}.workspaces w on w.id = p.id_workspace
        where w.name = %s
          and p.name = %s
          and p.type = %s
        ;'''
        with app.app_context():
            external_table_uri = db_util.run_query(query, (layer.workspace, layer.name, layer.type))[0][0]

        assert external_table_uri == {
            "db_uri_str": external_db.URI_STR,
            "schema": schema,
            "table": table,
            "geo_column": geo_column,
        }

        external_db.drop_table(schema, table)
