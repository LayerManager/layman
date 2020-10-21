import test.flask_client as client_util

from layman import settings, app as app
from . import ensure_schema, migrate_users_and_publications, model, publications as pub_util, users as user_util
from .util import run_query, run_statement
from layman import util
from layman.layer import util as layer_util
from layman.map import util as map_util

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
client = client_util.client


def test_recreate_schema(client):
    username = 'test_recreate_schema_user1'
    client_util.publish_layer(username, 'test_recreate_schema_layer1', client)
    client_util.publish_map(username, 'test_recreate_schema_map1', client)

    with app.app_context():
        run_statement(model.DROP_SCHEMA_SQL)
        ensure_schema()

    client_util.delete_layer(username, 'test_recreate_schema_layer1', client)
    client_util.delete_map(username, 'test_recreate_schema_map1', client)

    with app.app_context():
        pubs = layer_util.get_layer_infos(username)
        assert len(pubs) == 0
        pubs = map_util.get_map_infos(username)
        assert len(pubs) == 0


def test_schema(client):
    username = 'migration_test_user1'
    layername = 'migration_test_layer1'
    mapname = 'migration_test_map1'
    client_util.publish_layer(username, layername, client)
    client_util.publish_map(username, mapname, client)

    with app.app_context():
        run_statement(model.DROP_SCHEMA_SQL)
        ensure_schema()
        users = run_query(f'select count(*) from {DB_SCHEMA}.users;')
        assert users[0][0] == len(util.get_usernames())
        user_infos = user_util.get_user_infos()
        assert username in user_infos
        pub_infos = pub_util.get_publication_infos(username)
        assert layername in pub_infos
        assert mapname in pub_infos

    client_util.delete_layer(username, layername, client)
    client_util.delete_map(username, mapname, client)

    with app.app_context():
        pubs = layer_util.get_layer_infos(username)
        assert len(pubs) == 0
        pubs = map_util.get_map_infos(username)
        assert len(pubs) == 0


def test_steps(client):
    username = 'migration_test_user2'
    client_util.publish_layer(username, 'migration_test_layer2', client)
    client_util.publish_map(username, 'migration_test_map2', client)

    with app.app_context():
        run_statement(model.DROP_SCHEMA_SQL)
        exists_schema = run_query(model.EXISTS_SCHEMA_SQL)
        assert exists_schema[0][0] == 0

        run_statement(model.CREATE_SCHEMA_SQL)
        exists_schema = run_query(model.EXISTS_SCHEMA_SQL)
        assert exists_schema[0][0] == 1

        exists_right_types = run_query(f'select count(*) from {DB_SCHEMA}.right_types;')
        assert exists_right_types[0][0] == 0
        run_statement(model.setup_codelists_data())
        exists_right_types = run_query(f'select count(*) from {DB_SCHEMA}.right_types;')
        assert exists_right_types[0][0] == 2

        exists_users = run_query(f'select count(*) from {DB_SCHEMA}.users;')
        assert exists_users[0][0] == 0
        exists_pubs = run_query(f'select count(*) from {DB_SCHEMA}.publications;')
        assert exists_pubs[0][0] == 0
        migrate_users_and_publications()
        exists_users = run_query(f'select count(*) from {DB_SCHEMA}.users;')
        assert exists_users[0][0] > 0
        exists_pubs = run_query(f'select count(*) from {DB_SCHEMA}.publications;')
        assert exists_pubs[0][0] > 0

    client_util.delete_layer(username, 'migration_test_layer2', client)
    client_util.delete_map(username, 'migration_test_map2', client)
