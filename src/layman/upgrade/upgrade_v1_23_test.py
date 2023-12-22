import pytest

from db import util as db_util
from layman import app, settings
from layman.common.prime_db_schema import ensure_whole_user
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
    username = 'test_create_role_service_schema_username'
    rolename = f'USER_{username.upper()}'
    userinfo = {"issuer_id": 'mock_test_users_test',
                "sub": '10',
                "claims": {"email": "test@oauth2.org",
                           "name": "test ensure user",
                           "preferred_username": 'test_preferred',
                           "given_name": "test",
                           "family_name": "user",
                           "middle_name": "ensure",
                           }
                }
    drop_statement = f'''DROP SCHEMA IF EXISTS {ROLE_SERVICE_SCHEMA} CASCADE;'''
    schema_existence_query = f'''SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = '{ROLE_SERVICE_SCHEMA}';'''
    table_existence_query = f'''SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '{ROLE_SERVICE_SCHEMA}' and table_name = %s;'''
    layman_users_roles_query = f'''select COUNT(*) from {ROLE_SERVICE_SCHEMA}.layman_users_roles where name = %s'''
    layman_users_user_roles_query = f'''select COUNT(*) from {ROLE_SERVICE_SCHEMA}.layman_users_user_roles where username = %s and rolename = %s'''
    admin_roles_query = f'''select COUNT(*) from {ROLE_SERVICE_SCHEMA}.admin_roles'''
    admin_user_roles_query = f'''select COUNT(*) from {ROLE_SERVICE_SCHEMA}.admin_user_roles where username = %s and rolename = %s'''
    roles_query = f'''select
    (select count(*) from {ROLE_SERVICE_SCHEMA}.bussiness_roles) bussiness_roles,
    (select count(*) from {ROLE_SERVICE_SCHEMA}.layman_users_roles) layman_users_roles,
    (select count(*) from {ROLE_SERVICE_SCHEMA}.admin_roles) admin_roles,
    (select count(*) from {ROLE_SERVICE_SCHEMA}.roles) roles'''
    user_roles_query = f'''select
    (select count(*) from {ROLE_SERVICE_SCHEMA}.bussiness_user_roles) bussiness_user_roles,
    (select count(*) from {ROLE_SERVICE_SCHEMA}.layman_users_user_roles) layman_users_user_roles,
    (select count(*) from {ROLE_SERVICE_SCHEMA}.admin_user_roles) admin_user_roles,
    (select count(*) from {ROLE_SERVICE_SCHEMA}.user_roles) user_roles'''

    # prepare simple schema in the same way as in setup_geoserver.py
    prepare_simple_schema_statement = f"""
CREATE SCHEMA "{ROLE_SERVICE_SCHEMA}" AUTHORIZATION {settings.LAYMAN_PG_USER};
create view {ROLE_SERVICE_SCHEMA}.roles as select 'ADMIN'::varchar(64) as name, null::varchar(64) as parent
union all select 'GROUP_ADMIN', null
union all select %s, null
;
create view {ROLE_SERVICE_SCHEMA}.role_props as select null::varchar(64) as rolename, null::varchar(64) as propname, null::varchar(2048) as propvalue;
create view {ROLE_SERVICE_SCHEMA}.user_roles as select %s::varchar(64) as username, 'ADMIN'::varchar(64) as rolename
union all select %s, %s
union all select %s, 'ADMIN'
;
create view {ROLE_SERVICE_SCHEMA}.group_roles as select null::varchar(128) as groupname, null::varchar(64) as rolename;
    """

    with app.app_context():
        ensure_whole_user(username, userinfo)
        db_util.run_statement(drop_statement)
        result = db_util.run_query(schema_existence_query)[0][0]
        assert result == 0
        db_util.run_statement(prepare_simple_schema_statement, data=(
            settings.LAYMAN_GS_ROLE, settings.LAYMAN_GS_USER, settings.LAYMAN_GS_USER, settings.LAYMAN_GS_ROLE,
            settings.GEOSERVER_ADMIN_USER))

        upgrade_v1_23.create_role_service_schema()

        result = db_util.run_query(schema_existence_query)[0][0]
        assert result == 1
        result = db_util.run_query(table_existence_query, ('bussiness_roles',))[0][0]
        assert result == 1
        result = db_util.run_query(table_existence_query, ('bussiness_user_roles',))[0][0]
        assert result == 1
        result = db_util.run_query(layman_users_roles_query, (rolename,))[0][0]
        assert result == 1
        result = db_util.run_query(layman_users_user_roles_query, (username, rolename,))[0][0]
        assert result == 1
        result = db_util.run_query(admin_roles_query)[0][0]
        assert result == 3
        result = db_util.run_query(admin_user_roles_query, ('layman_test', 'LAYMAN_TEST_ROLE',))[0][0]
        assert result == 1
        result = db_util.run_query(admin_user_roles_query, ('layman_test', 'ADMIN',))[0][0]
        assert result == 1
        result = db_util.run_query(roles_query)[0]
        assert result[0] + result[1] + result[2] == result[3]
        result = db_util.run_query(user_roles_query)[0]
        assert result[0] + result[1] + result[2] == result[3]
        result = db_util.run_query(table_existence_query, ('role_props',))[0][0]
        assert result == 1
        result = db_util.run_query(table_existence_query, ('group_roles',))[0][0]
        assert result == 1
