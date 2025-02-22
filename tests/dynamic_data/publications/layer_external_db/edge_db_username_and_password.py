from urllib.parse import quote
from psycopg2 import sql
import pytest

from db import util as db_util
from layman import settings
from test_tools import process_client, external_db
from tests import EnumTestTypes, Publication4Test
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test, base_test_classes

USERNAME = 'external@#$%^&*_db_user'
PASSWORD = 'pass@#$%^&*word'
FILE_PATH = 'sample/layman.layer/small_layer.geojson'
SCHEMA = 'public'
TABLE = 'edge_username_password'

URI_STR = f'''postgresql://{quote(USERNAME)}:{quote(PASSWORD)}@{settings.LAYMAN_PG_HOST}:{settings.LAYMAN_PG_PORT}/{external_db.EXTERNAL_DB_NAME}'''

pytest_generate_tests = base_test.pytest_generate_tests


TEST_CASES = {
    'edge_username_password',
}


@pytest.mark.usefixtures('ensure_external_db')
class TestEdge(base_test.TestSingleRestPublication):

    workspace = 'edge_db_username_and_password_workspace'

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = []

    test_cases = [base_test.TestCaseType(
        key=key,
        type=EnumTestTypes.MANDATORY,
        rest_args={
            'external_table_uri': f"{URI_STR}"
                                  f"?schema={quote(SCHEMA)}"
                                  f"&table={quote(TABLE)}"
                                  f"&geo_column={quote(settings.OGR_DEFAULT_GEOMETRY_COLUMN)}",
        },
    ) for key in TEST_CASES]

    external_tables_to_create = [
        base_test_classes.ExternalTableDef(
            file_path=FILE_PATH,
            db_schema=SCHEMA,
            db_table=TABLE,
        ),
    ]

    def test_layer(self, layer: Publication4Test, rest_method, rest_args, ):
        """Parametrized using pytest_generate_tests"""
        statement = sql.SQL(f"""
        DO
        $$BEGIN
        IF ((SELECT count(*) FROM pg_roles WHERE rolname = {{username_value}}) > 0) THEN
            REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM {{username}};
            REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM {{username}};
            REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public FROM {{username}};
            REVOKE ALL PRIVILEGES ON DATABASE {external_db.EXTERNAL_DB_NAME} FROM {{username}};
        END IF;
        END$$;
        DROP USER IF EXISTS {{username}};
        CREATE USER {{username}} WITH PASSWORD {{password}};
        GRANT CONNECT ON DATABASE {external_db.EXTERNAL_DB_NAME} TO {{username}};
        GRANT SELECT ON {{schema}}.{{table}} TO {{username}};
        """).format(
            username=sql.Identifier(USERNAME),
            username_value=sql.Literal(USERNAME),
            password=sql.Literal(PASSWORD),
            schema=sql.Identifier(SCHEMA),
            table=sql.Identifier(TABLE),
        )
        db_util.run_statement(statement, uri_str=external_db.URI_STR)

        # publish layer from external DB table
        rest_method.fn(layer, args=rest_args)

        # general checks
        assert_util.is_publication_valid_and_complete(layer)
