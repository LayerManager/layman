import os
from urllib.parse import quote
import pytest

from db import util as db_util, TableUri
from layman import app, settings
from layman.util import get_publication_info
from test_tools import process_client, external_db
from tests import EnumTestTypes, Publication
from tests.asserts.final import publication as asserts_publ
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

DANGEROUS_NAME = '; DROP TABLE "public"."abc"; SELECT \'& Žlu-ťouč-ký\''

TEST_CASES = {
    'all': {
        'input_file_name': 'all',
        'style_file': None,
        'schema_name': 'public',
        'table_name': 'all',
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'GEOMETRY',
        'exp_native_bounding_box': [15.0, 49.0, 15.3, 49.3],
        'exp_bounding_box': [1669792.3618991035, 6274861.394006575, 1703188.2091370858, 6325919.274572152],
    },
    'geometrycollection_mixed_case_table_name': {
        'input_file_name': 'geometrycollection',
        'style_file': None,
        'schema_name': 'public',
        'table_name': 'MyGeometryCollection',
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'GEOMETRYCOLLECTION',
        'exp_native_bounding_box': [15.0, 45.0, 18.0, 46.0],
        'exp_bounding_box': [1669792.3618991035, 5621521.486192066, 2003750.8342789242, 5780349.220256351],
    },
    'linestring_dangerous_table_name': {
        'input_file_name': 'linestring',
        'style_file': None,
        'schema_name': 'public',
        'table_name': DANGEROUS_NAME,
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'LINESTRING',
        'exp_native_bounding_box': [15.0, 49.0, 15.3, 49.3],
        'exp_imported_into_GS': False,
    },
    'multilinestring_dangerous_schema_name': {
        'input_file_name': 'multilinestring',
        'style_file': None,
        'schema_name': DANGEROUS_NAME,
        'table_name': 'multilinestring',
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'MULTILINESTRING',
        'exp_native_bounding_box': [16.0, 47.0, 16.0, 48.5],
        'exp_imported_into_GS': False,
    },
    'multipoint_dangerous_geo_column_name': {
        'input_file_name': 'multipoint',
        'style_file': None,
        'schema_name': 'public',
        'table_name': 'multipoint',
        'geo_column_name': DANGEROUS_NAME,
        'exp_geometry_type': 'MULTIPOINT',
        'exp_native_bounding_box': [15.0, 47.8, 15.0, 48.0],
        'exp_imported_into_GS': False,
    },
    'multipolygon_qml': {
        'input_file_name': 'multipolygon',
        'style_file': 'tests/dynamic_data/publications/layer_external_db/multipolygon.qml',
        'schema_name': 'public',
        'table_name': 'multipolygon',
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'MULTIPOLYGON',
        'exp_native_bounding_box': [17.0, 47.0, 18.0, 48.5],
        'exp_bounding_box': [1892431.3434856508, 5942074.072431108, 2003750.8342789242, 6190443.809135445],
    },
    'point': {
        'input_file_name': 'point',
        'style_file': None,
        'schema_name': 'public',
        'table_name': 'point',
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'POINT',
        'exp_native_bounding_box': [15.0, 49.0, 15.3, 49.3],
        'exp_bounding_box': [1669792.3618991035, 6274861.394006575, 1703188.2091370858, 6325919.274572152],
    },
    'polygon': {
        'input_file_name': 'polygon',
        'style_file': None,
        'schema_name': 'public',
        'table_name': 'polygon',
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'POLYGON',
        'exp_native_bounding_box': [15.0, 49.0, 15.3, 49.3],
        'exp_bounding_box': [1669792.3618991035, 6274861.394006575, 1703188.2091370858, 6325919.274572152],
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
                                             'style_file': value['style_file'],
                                         },
                                         params=value,
                                         ) for key, value in TEST_CASES.items()]

    @staticmethod
    def test_layer(layer: Publication, key, rest_method, rest_args, params):
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

        with app.app_context():
            publ_info = get_publication_info(layer.workspace, layer.type, layer.name, context={'keys': [
                'table_uri', 'native_crs', 'native_bounding_box', 'wfs', 'wms', 'is_external_table',
            ], })
        table_uri = publ_info['_table_uri']
        assert table_uri == TableUri(
            db_uri_str=external_db.URI_STR,
            schema=schema,
            table=table,
            geo_column=geo_column,
        )

        assert publ_info['native_crs'] == 'EPSG:4326'
        assert publ_info['native_bounding_box'] == params['exp_native_bounding_box']
        assert publ_info['_is_external_table'] is True
        if params.get('exp_imported_into_GS', True):
            assert publ_info['wfs']['url'], f'publ_info={publ_info}'
            assert 'status' not in publ_info['wfs']
            assert 'wms' in publ_info, f'publ_info={publ_info}'
            assert publ_info['wms']['url'], f'publ_info={publ_info}'
            assert 'status' not in publ_info['wms']
            exp_thumbnail = os.path.join(DIRECTORY, f"thumbnail_{key}.png")
            asserts_publ.internal.thumbnail_equals(layer.workspace, layer.type, layer.name, exp_thumbnail, max_diffs=1)
            assert_util.is_publication_valid_and_complete(layer)
            style_type = os.path.splitext(rest_args['style_file'])[1][1:] if rest_args['style_file'] else 'sld'
            assert style_type in ['sld', 'qml']
            publ_type_detail = (settings.FILE_TYPE_VECTOR, style_type)
            asserts_publ.internal.correct_values_in_detail(layer.workspace, layer.type, layer.name,
                                                           publ_type_detail=publ_type_detail,
                                                           exp_publication_detail={
                                                               'bounding_box': params['exp_bounding_box'],
                                                               'native_crs': 'EPSG:4326',
                                                               'native_bounding_box': params['exp_native_bounding_box'],
                                                           },
                                                           external_table_uri=table_uri,
                                                           )

        external_db.drop_table(schema, table)
