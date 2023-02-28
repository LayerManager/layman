import pytest
import psycopg2
from psycopg2 import sql

from db import util as db_util
from layman import app, settings
from test_tools import process_client, external_db
from tests import EnumTestTypes, Publication
from tests.asserts.final.publication import util as assert_publ_util
from tests.dynamic_data import base_test

pytest_generate_tests = base_test.pytest_generate_tests


@pytest.mark.usefixtures('ensure_external_db')
class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'layer_info_unavailable_table_ws'

    publication_type = process_client.LAYER_TYPE

    test_cases = [base_test.TestCaseType(
        key='default',
        type=EnumTestTypes.MANDATORY,
        params=None
    )]

    def test_internal_layer(self, layer: Publication):
        self.post_publication(layer)
        assert_publ_util.is_publication_valid_and_complete(layer)

        # validate rest info pre
        rest_info_pre = process_client.get_workspace_layer(layer.workspace, layer.name)

        table_name = f"layer_{rest_info_pre['uuid'].replace('-', '_')}"
        assert rest_info_pre['db_table'] == {
            'name': table_name
        }
        assert rest_info_pre['db'] == {
            'schema': layer.workspace,
            'table': table_name,
            'geo_column': settings.OGR_DEFAULT_GEOMETRY_COLUMN,
        }

        # drop internal table
        statement = sql.SQL('DROP TABLE {table};').format(
            table=sql.Identifier(layer.workspace, table_name),
        )
        with app.app_context():
            db_util.run_statement(statement)

        rest_info_post = process_client.get_workspace_layer(layer.workspace, layer.name)

        assert rest_info_post['db_table'] == {
            'status': 'NOT_AVAILABLE',
        }
        assert rest_info_post['db'] == {
            'status': 'NOT_AVAILABLE',
        }

    def test_external_layer(self, layer: Publication):
        external_db_table = 'small_layer'
        external_db_schema = 'public'

        external_db.import_table(input_file_path='sample/layman.layer/small_layer.geojson',
                                 schema=external_db_schema,
                                 table=external_db_table,
                                 )
        self.post_publication(
            layer,
            args={
                'external_table_uri': f"{external_db.URI_STR}?schema={external_db_schema}&table={external_db_table}"
            }
        )
        assert_publ_util.is_publication_valid_and_complete(layer)

        # validate rest info pre
        rest_info_pre = process_client.get_workspace_layer(layer.workspace, layer.name)
        assert 'db_table' not in rest_info_pre
        assert rest_info_pre['db'] == {
            'schema': external_db_schema,
            'table': external_db_table,
            'geo_column': settings.OGR_DEFAULT_GEOMETRY_COLUMN,
            'external_uri': external_db.URI_STR_REDACTED,
        }

        # drop external table
        external_db.drop_table(schema=external_db_schema,
                               name=external_db_table)

        rest_info_post = process_client.get_workspace_layer(layer.workspace, layer.name)
        assert 'db_table' not in rest_info_pre
        assert rest_info_post['db'] == {
            'status': 'NOT_AVAILABLE',
            'error': 'Table does not exist.',
            'external_uri': 'postgresql://docker@postgresql:5432/external_test_db',
            'geo_column': 'wkb_geometry',
            'schema': 'public',
            'table': 'small_layer',
        }

        # disable external table connection
        new_db_uri_str = psycopg2.extras.Json({'db_uri_str': external_db.URI_STR_REDACTED})
        statement = sql.SQL("""update {prime_schema}.publications set
            external_table_uri = PGP_SYM_ENCRYPT((PGP_SYM_DECRYPT(external_table_uri::bytea, uuid::text)::jsonb || {new_db_uri_str})::text, uuid::text)
        where id_workspace = (select id from {prime_schema}.workspaces where name = {workspace})
          and name = {name}
          and type = {type}
        ;""").format(
            prime_schema=sql.Identifier(settings.LAYMAN_PRIME_SCHEMA),
            workspace=sql.Literal(layer.workspace),
            name=sql.Literal(layer.name),
            type=sql.Literal(layer.type),
            new_db_uri_str=sql.Literal(new_db_uri_str),
        )
        with app.app_context():
            db_util.run_statement(statement)

        rest_info_post = process_client.get_workspace_layer(layer.workspace, layer.name)
        assert 'db_table' not in rest_info_pre
        assert rest_info_post['db'] == {
            'status': 'NOT_AVAILABLE',
            'error': 'Cannot connect to DB.',
            'external_uri': 'postgresql://docker@postgresql:5432/external_test_db',
            'geo_column': 'wkb_geometry',
            'schema': 'public',
            'table': 'small_layer',
        }
