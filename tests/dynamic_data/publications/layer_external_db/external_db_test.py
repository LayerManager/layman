import os
from urllib.parse import quote
import pytest

from db import util as db_util
from layman import app, settings
from layman.map.prime_db_schema import get_workspaces
from layman.util import get_publication_info
from test_tools import process_client, external_db
from tests import EnumTestTypes, Publication4Test
from tests.asserts.final import publication as asserts_publ
from tests.asserts.final.publication import util as assert_util, geoserver as gs_asserts
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

EDGE_NAME = '__0_MyTest_CASE_AB7_'

TEST_CASES = {
    'all_unspecified_geocolumn': {
        'file_path': "sample/data/geometry-types/all.geojson",
        'style_file': None,
        'schema_name': 'public',
        'table_name': 'all',
        'primary_key_column': 'ogc_fid',
        'geo_column_name': 'wkb_geometry',
        'external_table_uri_str': f"{external_db.URI_STR}"
                                  f"?schema={quote('public')}"
                                  f"&table={quote('all')}",
        'additional_geo_column': None,
        'exp_thumbnail': os.path.join(DIRECTORY, f"thumbnail_all.png"),
        'exp_geometry_type': 'GEOMETRY',
        'exp_native_crs': 'EPSG:4326',
        'exp_native_bounding_box': [15.0, 49.0, 15.3, 49.3],
        'exp_bounding_box': [1669792.3618991035, 6274861.394006575, 1703188.2091370858, 6325919.274572152],
        'exp_languages': {'eng'},
        'exp_scale_denominator': 10_000_000,
        'mandatory_cases': {
            frozenset([base_test.RestMethod]),
        },
        'ignore_cases': {},
    },
    'geometrycollection_mixed_case_table_name_unspecified_geocolumn_with_2_geocolumns': {
        'file_path': "sample/data/geometry-types/geometrycollection.geojson",
        'style_file': None,
        'schema_name': 'public',
        'table_name': 'MyGeometryCollection',
        'primary_key_column': 'ogc_fid',
        'geo_column_name': 'wkb_geometry',
        'external_table_uri_str': f"{external_db.URI_STR}"
                                  f"?schema={quote('public')}"
                                  f"&table={quote('MyGeometryCollection')}",
        'additional_geo_column': 'wkb_geometry_2',
        'exp_thumbnail': os.path.join(DIRECTORY, f"thumbnail_geometrycollection.png"),
        'exp_geometry_type': 'GEOMETRYCOLLECTION',
        'exp_native_crs': 'EPSG:4326',
        'exp_native_bounding_box': [15.0, 45.0, 18.0, 46.0],
        'exp_bounding_box': [1669792.3618991035, 5621521.486192066, 2003750.8342789242, 5780349.220256351],
        'exp_languages': set(),
        'exp_scale_denominator': 100_000_000,
        'mandatory_cases': {},
        'ignore_cases': {},
    },
    'linestring_edge_all_names': {
        'file_path': "sample/data/geometry-types/linestring.geojson",
        'style_file': None,
        'schema_name': EDGE_NAME,
        'table_name': EDGE_NAME,
        'primary_key_column': 'ogc_fid',
        'geo_column_name': EDGE_NAME,
        'external_table_uri_str': None,
        'additional_geo_column': None,
        'exp_thumbnail': os.path.join(DIRECTORY, f"thumbnail_linestring.png"),
        'exp_geometry_type': 'LINESTRING',
        'exp_native_crs': 'EPSG:4326',
        'exp_native_bounding_box': [15.0, 49.0, 15.3, 49.3],
        'exp_bounding_box': [1669792.3618991035, 6274861.394006575, 1703188.2091370858, 6325919.274572152],
        'exp_languages': set(),
        'exp_scale_denominator': 25_000_000,
        'mandatory_cases': {},
        'ignore_cases': {
            frozenset([base_test.RestMethod.PATCH]),
        },
    },
    'multipolygon_qml_custom_id_column_custom_geo_column': {
        'file_path': "sample/data/geometry-types/multipolygon.geojson",
        'style_file': 'tests/dynamic_data/publications/layer_external_db/multipolygon.qml',
        'schema_name': 'public',
        'table_name': 'multipolygon',
        'primary_key_column': 'my_id',
        'external_table_uri_str': None,
        'additional_geo_column': None,
        'exp_thumbnail': os.path.join(DIRECTORY, f"thumbnail_multipolygon_qml.png"),
        'geo_column_name': 'my_geometry',
        'exp_geometry_type': 'MULTIPOLYGON',
        'exp_native_crs': 'EPSG:4326',
        'exp_native_bounding_box': [17.0, 47.0, 18.0, 48.5],
        'exp_bounding_box': [1892431.3434856508, 5942074.072431108, 2003750.8342789242, 6190443.809135445],
        'exp_languages': {'eng', 'cze'},
        'exp_scale_denominator': 50_000_000,
        'mandatory_cases': {
            frozenset([base_test.RestMethod]),
        },
        'ignore_cases': {},
    },
    'point_epsg_5514_qml': {
        'file_path': "tests/dynamic_data/publications/crs/vectors/sample_point_cz_5514.shp",
        'style_file': 'tests/dynamic_data/publications/crs/vectors/sample_point_cz.qml',
        'schema_name': 'public',
        'table_name': 'point_5514',
        'primary_key_column': 'ogc_fid',
        'geo_column_name': 'wkb_geometry',
        'external_table_uri_str': None,
        'additional_geo_column': None,
        'exp_thumbnail': 'tests/dynamic_data/publications/crs/vectors/sample_point_cz_5514_thumbnail.png',
        'exp_geometry_type': 'POINT',
        'exp_native_crs': 'EPSG:5514',
        'exp_native_bounding_box': [-598214.7290553625, -1160319.8064114263, -598200.932166816, -1160307.4425631783],
        'exp_bounding_box': [1848640.4769060146, 6308683.577507495, 1848663.461145939, 6308704.681240051],
        'exp_languages': set(),
        'exp_scale_denominator': None,  # Layman doesn't guess scale denominator for (multi)points
        'mandatory_cases': {},
        'ignore_cases': {
            frozenset([base_test.RestMethod.PATCH]),
        },
    },
    'point_epsg_3034': {
        'file_path': "tests/dynamic_data/publications/crs/vectors/sample_point_cz_3034.shp",
        'style_file': 'tests/dynamic_data/publications/crs/vectors/sample_point_cz.sld',
        'schema_name': 'public',
        'table_name': 'point_3034',
        'primary_key_column': 'ogc_fid',
        'geo_column_name': 'wkb_geometry',
        'external_table_uri_str': None,
        'additional_geo_column': None,
        'exp_thumbnail': 'tests/dynamic_data/publications/crs/vectors/sample_point_cz_3034_thumbnail.png',
        'exp_geometry_type': 'POINT',
        'exp_native_crs': 'EPSG:3034',
        'exp_native_bounding_box': [4464506.142159825, 2519866.800920298, 4464518.794200855, 2519878.8700591023],
        'exp_bounding_box': [1848640.5623333207, 6308683.148403931, 1848662.1915096296, 6308704.001720284],
        'exp_languages': set(),
        'exp_scale_denominator': None,  # Layman doesn't guess scale denominator for (multi)points
        'mandatory_cases': {
            frozenset([base_test.RestMethod.POST]),
        },
        'ignore_cases': {},
    },
    'point_epsg_3034_qml': {
        'file_path': "tests/dynamic_data/publications/crs/vectors/sample_point_cz_3034.shp",
        'style_file': 'tests/dynamic_data/publications/crs/vectors/sample_point_cz.qml',
        'schema_name': 'public',
        'table_name': 'point_3034_qml',
        'primary_key_column': 'ogc_fid',
        'geo_column_name': 'wkb_geometry',
        'external_table_uri_str': None,
        'additional_geo_column': None,
        'exp_thumbnail': 'tests/dynamic_data/publications/layer_external_db/thumbnail_point_3034_qml.png',
        'exp_geometry_type': 'POINT',
        'exp_native_crs': 'EPSG:3034',
        'exp_native_bounding_box': [4464506.142159825, 2519866.800920298, 4464518.794200855, 2519878.8700591023],
        'exp_bounding_box': [1848640.5623333207, 6308683.148403931, 1848662.1915096296, 6308704.001720284],
        'exp_languages': set(),
        'exp_scale_denominator': None,  # Layman doesn't guess scale denominator for (multi)points
        'mandatory_cases': {
            frozenset([base_test.RestMethod.POST]),
        },
        'ignore_cases': {},
    },
}


@pytest.mark.usefixtures('ensure_external_db')
class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_layer_external_db_geometry_type'

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = [
        base_test.RestMethod,
    ]

    test_cases = [base_test.TestCaseType(
        key=key,
        type=EnumTestTypes.OPTIONAL,
        rest_args={
            'external_table_uri': value['external_table_uri_str'] or f"{external_db.URI_STR}"
                                                                     f"?schema={quote(value['schema_name'])}"
                                                                     f"&table={quote(value['table_name'])}"
                                                                     f"&geo_column={quote(value['geo_column_name'])}",
            'style_file': value['style_file'],
        },
        params=value,
        specific_types={
            **{
                case: EnumTestTypes.IGNORE
                for case in value['ignore_cases']
            },
            **{
                case: EnumTestTypes.MANDATORY
                for case in value['mandatory_cases']
            },
        },
    ) for key, value in TEST_CASES.items()]

    def test_layer(self, layer: Publication4Test, rest_method, rest_args, params):
        """Parametrized using pytest_generate_tests"""
        schema = params['schema_name']
        table = params['table_name']
        geo_column = params['geo_column_name']
        primary_key_column = params['primary_key_column']

        # import data into external DB
        self.import_external_table(params['file_path'], {
            'schema': schema,
            'table': table,
            'geo_column': geo_column,
            'primary_key_column': primary_key_column,
            'additional_geo_column': params['additional_geo_column'],
        })
        query = f'''select type from geometry_columns where f_table_schema = %s and f_table_name = %s and f_geometry_column = %s'''
        result = db_util.run_query(query, (schema, table, geo_column), uri_str=external_db.URI_STR)
        assert result[0][0] == params['exp_geometry_type']

        # publish layer from external DB table
        rest_method.fn(layer, args=rest_args)

        # general checks
        assert_util.is_publication_valid_and_complete(layer)
        with app.app_context():
            publ_info = get_publication_info(layer.workspace, layer.type, layer.name,
                                             context={'keys': ['table_uri', 'uuid']})
        table_uri = publ_info['_table_uri']
        uuid = publ_info['uuid']
        style_type = os.path.splitext(rest_args['style_file'])[1][1:] if rest_args['style_file'] else 'sld'
        assert style_type in ['sld', 'qml']
        publ_type_detail = (settings.GEODATA_TYPE_VECTOR, style_type)
        asserts_publ.internal.correct_values_in_detail(layer.workspace, layer.type, layer.name,
                                                       publ_type_detail=publ_type_detail,
                                                       exp_publication_detail={
                                                           'bounding_box': params['exp_bounding_box'],
                                                           'native_crs': params['exp_native_crs'],
                                                           'native_bounding_box': params['exp_native_bounding_box'],
                                                       },
                                                       external_table_uri=table_uri,
                                                       )

        # check thumbnail
        exp_thumbnail = params['exp_thumbnail']
        asserts_publ.internal.thumbnail_equals(layer.workspace, layer.type, layer.name, exp_thumbnail, max_diffs=1)

        # check GeoServer store of external DB exists
        workspaces = get_workspaces()
        all_db_stores = {f'postgresql_{workspace}' for workspace in workspaces}
        both_db_stores = all_db_stores.union({f'external_db_{uuid}'})
        exp_wms_stores = both_db_stores if style_type == 'sld' else all_db_stores
        gs_asserts.assert_stores(exp_wfs_stores=both_db_stores, exp_wms_stores=exp_wms_stores)

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
        gs_asserts.assert_stores(exp_wfs_stores=all_db_stores, exp_wms_stores=all_db_stores)

        # check there is no information about the layer anymore
        with app.app_context():
            publ_info = get_publication_info(layer.workspace, layer.type, layer.name)
        assert not publ_info

        # clean up external DB table
        external_db.drop_table(schema, table)
