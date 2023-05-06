import os
from urllib.parse import quote
import pytest

from db import TableUri
from layman import settings
from test_tools import process_client, external_db
from tests import Publication, EnumTestTypes, EnumTestKeys
from tests.asserts.final import publication as asserts_publ
from tests.asserts.final.publication import util as assert_util, geoserver as gs_asserts
from tests.dynamic_data import base_test, base_test_classes
from .. import common_publications

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

DB_SCHEMA = 'public'
TABLE_POST = 'all_patch'
TABLE_PATCH = 'multipolygon_patch'
GEO_COLUMN = settings.OGR_DEFAULT_GEOMETRY_COLUMN

TEST_CASES = {
    'only_title': {
        EnumTestKeys.TYPE: EnumTestTypes.MANDATORY,
        'patch_args': {
            'title': 'New title',
        },
        'exp_thumbnail': os.path.join(DIRECTORY, f"thumbnail_all.png"),
        'exp_info_values': {
            'publ_type_detail': (settings.GEODATA_TYPE_VECTOR, 'sld'),
            'exp_publication_detail': {
                'title': 'New title',
                'bounding_box': [1669792.3618991035, 6274861.394006575, 1703188.2091370858, 6325919.274572152],
                'native_crs': 'EPSG:4326',
                'native_bounding_box': [15.0, 49.0, 15.3, 49.3],
            },
            'external_table_uri': TableUri(
                db_uri_str=external_db.URI_STR,
                schema=DB_SCHEMA,
                table=TABLE_POST,
                geo_column=settings.OGR_DEFAULT_GEOMETRY_COLUMN,
                primary_key_column=settings.OGR_DEFAULT_PRIMARY_KEY,
            ),
        },
    },
    'internal_vector': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        'patch_args': {
            'file_paths': ['sample/layman.layer/small_layer.geojson'],
        },
        'exp_thumbnail': common_publications.LAYER_VECTOR_SLD.thumbnail,
        'exp_info_values': common_publications.LAYER_VECTOR_SLD.info_values,
    },
    'internal_raster': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        'patch_args': common_publications.LAYER_RASTER.definition,
        'exp_thumbnail': common_publications.LAYER_RASTER.thumbnail,
        'exp_info_values': common_publications.LAYER_RASTER.info_values,
    },
    'other_external_table_qml': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        'patch_args': {
            'external_table_uri': f"{external_db.URI_STR}"
                                  f"?schema={DB_SCHEMA}"
                                  f"&table={TABLE_PATCH}"
                                  f"&geo_column={GEO_COLUMN}",
            'style_file': 'tests/dynamic_data/publications/layer_external_db/multipolygon.qml',
        },
        'exp_thumbnail': os.path.join(DIRECTORY, f"thumbnail_multipolygon_qml.png"),
        'exp_info_values': {
            'publ_type_detail': (settings.GEODATA_TYPE_VECTOR, 'qml'),
            'exp_publication_detail': {
                'bounding_box': [1892431.3434856508, 5942074.072431108, 2003750.8342789242, 6190443.809135445],
                'native_crs': 'EPSG:4326',
                'native_bounding_box': [17.0, 47.0, 18.0, 48.5],
            },
            'external_table_uri': TableUri(
                db_uri_str=external_db.URI_STR,
                schema=DB_SCHEMA,
                table=TABLE_PATCH,
                geo_column=settings.OGR_DEFAULT_GEOMETRY_COLUMN,
                primary_key_column=settings.OGR_DEFAULT_PRIMARY_KEY,
            ),
        },
    },
}


@pytest.mark.usefixtures('ensure_external_db')
class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_layer_patch_after_external_db'

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = []

    test_cases = [base_test.TestCaseType(key=key,
                                         type=value[EnumTestKeys.TYPE],
                                         rest_args=value['patch_args'],
                                         params=value,
                                         ) for key, value in TEST_CASES.items()]

    external_tables_to_create = [base_test_classes.ExternalTableDef(file_path="sample/data/geometry-types/all.geojson",
                                                                    db_schema=DB_SCHEMA,
                                                                    db_table=TABLE_POST,),
                                 base_test_classes.ExternalTableDef(file_path="sample/data/geometry-types/multipolygon.geojson",
                                                                    db_schema=DB_SCHEMA,
                                                                    db_table=TABLE_PATCH,),
                                 ]

    def test_layer(self, layer: Publication, rest_args, params):
        """Parametrized using pytest_generate_tests"""
        external_table_uri = f"{external_db.URI_STR}?schema={quote(DB_SCHEMA)}&table={quote(TABLE_POST)}&geo_column={GEO_COLUMN}"
        self.post_publication(publication=layer,
                              args={'external_table_uri': external_table_uri})

        assert_util.is_publication_valid_and_complete(layer)
        exp_thumbnail = os.path.join(DIRECTORY, f"thumbnail_all.png")
        asserts_publ.internal.thumbnail_equals(layer.workspace, layer.type, layer.name, exp_thumbnail, max_diffs=1)

        self.patch_publication(publication=layer,
                               args=rest_args)

        assert_util.is_publication_valid_and_complete(layer)
        exp_thumbnail = params['exp_thumbnail']
        asserts_publ.internal.thumbnail_equals(layer.workspace, layer.type, layer.name, exp_thumbnail, max_diffs=5)

        asserts_publ.internal.correct_values_in_detail(layer.workspace, layer.type, layer.name,
                                                       **params['exp_info_values'],
                                                       )

        exp_existing_wfs_stores = {'postgresql', f'external_db_{layer.name}'} if params['exp_info_values'].get('external_table_uri') else {'postgresql'}
        exp_deleted_wfs_stores = {} if params['exp_info_values'].get('external_table_uri') else {f'external_db_{layer.name}'}
        exp_existing_wms_stores = {'postgresql', f'external_db_{layer.name}'} if params['exp_info_values'].get('external_table_uri') and params['exp_info_values']['publ_type_detail'][1] == 'sld' else {'postgresql'}
        exp_deleted_wms_stores = {} if params['exp_info_values'].get('external_table_uri') and params['exp_info_values']['publ_type_detail'][1] == 'sld' else {f'external_db_{layer.name}'}
        gs_asserts.assert_stores(layer.workspace,
                                 exp_existing_wfs_stores=exp_existing_wfs_stores, exp_deleted_wfs_stores=exp_deleted_wfs_stores,
                                 exp_existing_wms_stores=exp_existing_wms_stores, exp_deleted_wms_stores=exp_deleted_wms_stores,
                                 )
