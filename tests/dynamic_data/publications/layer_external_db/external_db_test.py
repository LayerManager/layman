import os
from urllib.parse import quote
import pytest

from db import util as db_util
from geoserver import util as gs_util
from layman import app, settings
from layman.util import get_publication_info
from test_tools import process_client, external_db
from tests import EnumTestTypes, Publication
from tests.asserts.final import publication as asserts_publ
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

EDGE_NAME = '__0_MyTest_CASE_AB7_'

TEST_CASES = {
    'all': {
        'input_file_name': 'all',
        'style_file': None,
        'schema_name': 'public',
        'table_name': 'all',
        'primary_key_column': 'ogc_fid',
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'GEOMETRY',
        'exp_native_bounding_box': [15.0, 49.0, 15.3, 49.3],
        'exp_bounding_box': [1669792.3618991035, 6274861.394006575, 1703188.2091370858, 6325919.274572152],
        'exp_languages': {'eng'},
        'exp_scale_denominator': 10_000_000,
    },
    'geometrycollection_mixed_case_table_name': {
        'input_file_name': 'geometrycollection',
        'style_file': None,
        'schema_name': 'public',
        'table_name': 'MyGeometryCollection',
        'primary_key_column': 'ogc_fid',
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'GEOMETRYCOLLECTION',
        'exp_native_bounding_box': [15.0, 45.0, 18.0, 46.0],
        'exp_bounding_box': [1669792.3618991035, 5621521.486192066, 2003750.8342789242, 5780349.220256351],
        'exp_languages': set(),
        'exp_scale_denominator': 100_000_000,
    },
    'linestring_edge_table_name': {
        'input_file_name': 'linestring',
        'style_file': None,
        'schema_name': 'public',
        'table_name': EDGE_NAME,
        'primary_key_column': 'ogc_fid',
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'LINESTRING',
        'exp_native_bounding_box': [15.0, 49.0, 15.3, 49.3],
        'exp_bounding_box': [1669792.3618991035, 6274861.394006575, 1703188.2091370858, 6325919.274572152],
        'exp_languages': set(),
        'exp_scale_denominator': 25_000_000,
    },
    'multilinestring_edge_schema_name': {
        'input_file_name': 'multilinestring',
        'style_file': None,
        'schema_name': EDGE_NAME,
        'table_name': 'multilinestring',
        'primary_key_column': 'ogc_fid',
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'MULTILINESTRING',
        'exp_native_bounding_box': [15.0, 47.0, 16.0, 48.5],
        'exp_bounding_box': [1669792.3618991035, 5942074.072431108, 1781111.852692377, 6190443.809135445],
        'exp_languages': set(),
        'exp_scale_denominator': 100_000_000,
    },
    'multipoint_edge_geo_column_name': {
        'input_file_name': 'multipoint',
        'style_file': None,
        'schema_name': 'public',
        'table_name': 'multipoint',
        'primary_key_column': 'ogc_fid',
        'geo_column_name': EDGE_NAME,
        'exp_geometry_type': 'MULTIPOINT',
        'exp_native_bounding_box': [15.0, 47.8, 16.0, 48.0],
        'exp_bounding_box': [1669792.3618991035, 6073646.223350629, 1781111.852692377, 6106854.834885075],
        'exp_languages': set(),
        'exp_scale_denominator': None,  # Layman doesn't guess scale denominator for (multi)points
    },
    'multipolygon_qml_custom_id_column': {
        'input_file_name': 'multipolygon',
        'style_file': 'tests/dynamic_data/publications/layer_external_db/multipolygon.qml',
        'schema_name': 'public',
        'table_name': 'multipolygon',
        'primary_key_column': 'my_id',
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'MULTIPOLYGON',
        'exp_native_bounding_box': [17.0, 47.0, 18.0, 48.5],
        'exp_bounding_box': [1892431.3434856508, 5942074.072431108, 2003750.8342789242, 6190443.809135445],
        'exp_languages': {'eng', 'cze'},
        'exp_scale_denominator': 50_000_000,
    },
    'point_custom_id_column': {
        'input_file_name': 'point',
        'style_file': None,
        'schema_name': 'public',
        'table_name': 'point',
        'primary_key_column': 'my_id2',
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'POINT',
        'exp_native_bounding_box': [15.0, 49.0, 15.3, 49.3],
        'exp_bounding_box': [1669792.3618991035, 6274861.394006575, 1703188.2091370858, 6325919.274572152],
        'exp_languages': set(),
        'exp_scale_denominator': None,  # Layman doesn't guess scale denominator for (multi)points
    },
    'polygon': {
        'input_file_name': 'polygon',
        'style_file': None,
        'schema_name': 'public',
        'table_name': 'polygon',
        'primary_key_column': 'ogc_fid',
        'geo_column_name': 'wkb_geometry',
        'exp_geometry_type': 'POLYGON',
        'exp_native_bounding_box': [15.0, 49.0, 15.3, 49.3],
        'exp_bounding_box': [1669792.3618991035, 6274861.394006575, 1703188.2091370858, 6325919.274572152],
        'exp_languages': set(),
        'exp_scale_denominator': 10_000_000,
    },
}


def assert_stores(workspace, exp_stores):
    stores = gs_util.get_db_stores(geoserver_workspace=workspace,
                                   auth=settings.LAYMAN_GS_AUTH,
                                   )
    store_names = {store['name'] for store in stores['dataStores']['dataStore']}
    assert store_names == exp_stores, f'workspace={workspace}, store_names={store_names}, exp_stores={exp_stores}'


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
        primary_key_column = params['primary_key_column']

        # import data into external DB
        external_db.import_table(file_path, table=table, schema=schema, geo_column=geo_column,
                                 primary_key_column=primary_key_column)
        conn_cur = db_util.create_connection_cursor(external_db.URI_STR)
        query = f'''select type from geometry_columns where f_table_schema = %s and f_table_name = %s and f_geometry_column = %s'''
        result = db_util.run_query(query, (schema, table, geo_column), conn_cur=conn_cur)
        assert result[0][0] == params['exp_geometry_type']

        # publish layer from external DB table
        rest_method(layer, args=rest_args)

        # general checks
        assert_util.is_publication_valid_and_complete(layer)
        with app.app_context():
            publ_info = get_publication_info(layer.workspace, layer.type, layer.name,
                                             context={'keys': ['table_uri']})
        table_uri = publ_info['_table_uri']
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

        # check thumbnail
        exp_thumbnail = os.path.join(DIRECTORY, f"thumbnail_{key}.png")
        asserts_publ.internal.thumbnail_equals(layer.workspace, layer.type, layer.name, exp_thumbnail, max_diffs=1)

        # check GeoServer store of external DB exists
        only_default_db_store = {'postgresql'}
        both_db_stores = {'postgresql', f'external_db_{layer.name}'}
        exp_wms_stores = both_db_stores if style_type == 'sld' else only_default_db_store
        assert_stores(workspace=layer.workspace, exp_stores=both_db_stores)
        assert_stores(workspace=f'{layer.workspace}_wms', exp_stores=exp_wms_stores)

        # check metadata properties language and scale_denominator (they are derived from DB)
        comp = process_client.get_workspace_publication_metadata_comparison(layer.type, layer.workspace, layer.name)
        md_lang = comp['metadata_properties']['language']
        assert md_lang['equal'] is True
        assert all(set(langs) == params['exp_languages'] for langs in md_lang['values'].values()), \
            f"langs={md_lang['values'].values()}, exp_langs={params['exp_languages']}"
        md_spatial_res = comp['metadata_properties']['spatial_resolution']
        assert md_spatial_res['equal'] is True
        exp_sp_res = {
            'scale_denominator': params['exp_scale_denominator']
        } if params['exp_scale_denominator'] is not None else None
        assert all(sp_res == exp_sp_res for sp_res in md_spatial_res['values'].values()), \
            f"sp_res={md_spatial_res['values'].values()}, exp_sp_res={exp_sp_res}"

        # delete layer from external DB table
        process_client.delete_workspace_layer(layer.workspace, layer.name)

        # check GeoServer store of external DB does not exist anymore
        assert_stores(workspace=layer.workspace, exp_stores=only_default_db_store)
        assert_stores(workspace=f'{layer.workspace}_wms', exp_stores=only_default_db_store)

        # check there is no information about the layer anymore
        with app.app_context():
            publ_info = get_publication_info(layer.workspace, layer.type, layer.name)
        assert not publ_info

        # clean up external DB table
        external_db.drop_table(schema, table)
