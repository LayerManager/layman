import pytest

from db import util as db_util
from layman import app, settings
from test_tools import process_client
from . import upgrade_v1_23

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
ROLE_SERVICE_SCHEMA = settings.LAYMAN_INTERNAL_ROLE_SERVICE_SCHEMA


@pytest.mark.usefixtures('ensure_layman', 'oauth2_provider_mock')
def test_adjust_db_for_roles():
    username = 'test_adjust_db_for_roles_ws'
    username2 = 'test_adjust_db_for_roles_ws2'
    layer_name = 'test_adjust_db_for_roles_layer'

    headers = process_client.get_authz_headers(username)
    process_client.reserve_username(username, headers=headers)
    headers2 = process_client.get_authz_headers(username2)
    process_client.reserve_username(username2, headers=headers2)

    process_client.publish_workspace_layer(username, layer_name, headers=headers, access_rights={
        'read': f"{username},{username2}",
    })

    statement = f'''
ALTER TABLE {DB_SCHEMA}.rights ALTER COLUMN id_user SET NOT NULL;
ALTER TABLE {DB_SCHEMA}.rights DROP CONSTRAINT rights_role_xor_user;
ALTER TABLE {DB_SCHEMA}.rights DROP CONSTRAINT rights_unique_key;
ALTER TABLE {DB_SCHEMA}.rights ADD CONSTRAINT rights_unique_key unique (id_user, id_publication, type);
ALTER TABLE {DB_SCHEMA}.rights DROP COLUMN role_name;
    '''
    with app.app_context():
        db_util.run_statement(statement)

    query = f'''select * from {DB_SCHEMA}.rights;'''
    with app.app_context():
        rights_rows = db_util.run_query(query)
    assert len(rights_rows[0]) == 4, f"Exactly 4 columns expected before migration"

    with app.app_context():
        upgrade_v1_23.adjust_db_for_roles()

    query = f'''
select id, id_user, role_name, id_publication, type
from {DB_SCHEMA}.rights
where id_publication in (
    select id from {DB_SCHEMA}.publications
    where name='{layer_name}'
        and id_workspace in (
            select id from {DB_SCHEMA}.workspaces
            where name='{username}'
        )
)
'''
    with app.app_context():
        rights_rows = db_util.run_query(query)
    assert len(rights_rows) == 1
    assert rights_rows[0][1] is not None, f"id_user is none!"
    assert rights_rows[0][2] is None, f"role_name is not none!"


def test_create_role_service_schema():
    drop_statement = f'''DROP SCHEMA IF EXISTS {ROLE_SERVICE_SCHEMA};'''
    schema_existence_query = f'''SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{ROLE_SERVICE_SCHEMA}';'''
    with app.app_context():
        db_util.run_statement(drop_statement)
        result = len(db_util.run_query(schema_existence_query))
        assert result == 0

        upgrade_v1_23.create_role_service_schema()

        result = len(db_util.run_query(schema_existence_query))
        assert result == 1
