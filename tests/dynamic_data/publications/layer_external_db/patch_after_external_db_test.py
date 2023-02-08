import os
from urllib.parse import quote
import pytest

from layman import settings
from test_tools import process_client, external_db
from tests import EnumTestTypes, Publication
from tests.asserts.final import publication as asserts_publ
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test
from .. import common_publications

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

DB_SCHEMA = 'public'
TABLE_POST = 'all_patch'
TABLE_PATCH = 'multipolygon_patch'
GEO_COLUMN = settings.OGR_DEFAULT_GEOMETRY_COLUMN

TEST_CASES = {
    'other_external_table': {
        'patch_args': {
            'db_connection': f"{external_db.URI_STR}"
                             f"?schema={DB_SCHEMA}"
                             f"&table={TABLE_PATCH}"
                             f"&geo_column={GEO_COLUMN}"
        },
        'exp_thumbnail': os.path.join(DIRECTORY, f"thumbnail_multipolygon_sld.png"),
    },
    'only_title': {
        'patch_args': {
            'title': 'New title',
        },
        'exp_thumbnail': os.path.join(DIRECTORY, f"thumbnail_all.png"),
    },
    'internal_vector': {
        'patch_args': {
            'file_paths': ['sample/layman.layer/small_layer.geojson'],
        },
        'exp_thumbnail': common_publications.LAYER_VECTOR_SLD.thumbnail,
    },
    'internal_raster': {
        'patch_args': common_publications.LAYER_RASTER.definition,
        'exp_thumbnail': common_publications.LAYER_RASTER.thumbnail,
    },
    'other_external_table_qml': {
        'patch_args': {
            'db_connection': f"{external_db.URI_STR}"
                             f"?schema={DB_SCHEMA}"
                             f"&table={TABLE_PATCH}"
                             f"&geo_column={GEO_COLUMN}",
            'style_file': 'tests/dynamic_data/publications/layer_external_db/multipolygon.qml',
        },
        'exp_thumbnail': os.path.join(DIRECTORY, f"thumbnail_multipolygon_qml_custom_id_column.png"),
    },
}


@pytest.fixture(scope="session")
def ensure_external_table():
    external_db.import_table(f"sample/data/geometry-types/all.geojson",
                             table=TABLE_POST,
                             schema=DB_SCHEMA)
    external_db.import_table(f"sample/data/geometry-types/multipolygon.geojson",
                             table=TABLE_PATCH,
                             schema=DB_SCHEMA)
    yield
    external_db.drop_table(DB_SCHEMA, TABLE_POST)
    external_db.drop_table(DB_SCHEMA, TABLE_PATCH)


@pytest.mark.usefixtures('ensure_external_db', 'ensure_external_table')
class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_layer_external_db_geometry_type'

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = []

    test_cases = [base_test.TestCaseType(key=key,
                                         type=EnumTestTypes.MANDATORY,
                                         rest_args=value['patch_args'],
                                         params=value,
                                         ) for key, value in TEST_CASES.items()]

    @staticmethod
    def test_layer(layer: Publication, rest_args, params):
        """Parametrized using pytest_generate_tests"""
        db_connection = f"{external_db.URI_STR}?schema={quote(DB_SCHEMA)}&table={quote(TABLE_POST)}&geo_column={GEO_COLUMN}"
        process_client.publish_workspace_publication(publication_type=layer.type,
                                                     workspace=layer.workspace,
                                                     name=layer.name,
                                                     db_connection=db_connection,
                                                     )

        assert_util.is_publication_valid_and_complete(layer)
        exp_thumbnail = os.path.join(DIRECTORY, f"thumbnail_all.png")
        asserts_publ.internal.thumbnail_equals(layer.workspace, layer.type, layer.name, exp_thumbnail, max_diffs=1)

        process_client.patch_workspace_publication(publication_type=layer.type,
                                                   workspace=layer.workspace,
                                                   name=layer.name,
                                                   **rest_args,
                                                   )

        assert_util.is_publication_valid_and_complete(layer)
        exp_thumbnail = params['exp_thumbnail']
        asserts_publ.internal.thumbnail_equals(layer.workspace, layer.type, layer.name, exp_thumbnail, max_diffs=5)
