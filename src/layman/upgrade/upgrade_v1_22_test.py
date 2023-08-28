import pytest

from db import util as db_util
from layman import app, settings
from test_tools import process_client
from . import upgrade_v1_22

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


@pytest.mark.usefixtures('ensure_layman', 'oauth2_provider_mock')
def test_fix_issuer_id():
    username = 'test_fix_issuer_id_user'

    headers = process_client.get_authz_headers(username)
    process_client.reserve_username(username, headers=headers)

    statement = f'''update {DB_SCHEMA}.users set issuer_id = 'layman.authn.oauth2.liferay';'''
    with app.app_context():
        db_util.run_statement(statement)

    query = f'''select distinct issuer_id from {DB_SCHEMA}.users;'''
    with app.app_context():
        issuer_id_rows = db_util.run_query(query)
    assert len(issuer_id_rows) == 1
    assert issuer_id_rows[0][0] == 'layman.authn.oauth2.liferay'

    with app.app_context():
        upgrade_v1_22.fix_issuer_id()

    query = f'''select distinct issuer_id from {DB_SCHEMA}.users;'''
    with app.app_context():
        issuer_id_rows = db_util.run_query(query)
    assert len(issuer_id_rows) == 1
    assert issuer_id_rows[0][0] == 'layman.authn.oauth2'


@pytest.mark.usefixtures('ensure_layman')
def test_insert_map_layer_relations():
    workspace = 'test_insert_map_layer_relations_workspace'
    map_name = 'test_insert_map_layer_relations_map'
    process_client.publish_workspace_map(workspace, map_name, file_paths=['sample/layman.map/internal_url.json'])

    query_map_id = f'''
    select p.id
    from {DB_SCHEMA}.publications p inner join
         {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
    where w.name = %s
      and p.name = %s
    ;
    '''
    with app.app_context():
        map_id = db_util.run_query(query_map_id, (workspace, map_name))[0][0]

    statement_truncate = f'''truncate table {DB_SCHEMA}.map_layer;'''
    with app.app_context():
        db_util.run_statement(statement_truncate)

    query_count = f'''select count(*) from {DB_SCHEMA}.map_layer;'''
    with app.app_context():
        map_layer_cnt = db_util.run_query(query_count)
    assert map_layer_cnt == [(0, )]

    with app.app_context():
        upgrade_v1_22.insert_map_layer_relations()

    query_map_layers = f'''select id_map, layer_workspace, layer_name, layer_index from {DB_SCHEMA}.map_layer order by layer_index asc'''
    with app.app_context():
        map_layers = db_util.run_query(query_map_layers)
    assert map_layers == [
        (map_id, 'testuser1', 'hranice', 1),
        (map_id, 'testuser1', 'mista', 2)
    ]
