from test.flask_client import client
import test.flask_client as client_util

from layman import settings, app as app
from . import ensure_schema, migrate_users_with_publications, model
from .utils import run_query, run_statement
from layman.util import get_usernames

DB_SCHEMA = settings.PG_LAYMAN_SCHEMA


def test_recreate_schema(client):
    with app.app_context():
        run_statement(model.DROP_SCHEMA_SQL)
        ensure_schema()


def test_schema(client):
    username = 'migration_test_user1'
    with app.app_context():
        client_util.publish_layer(username, 'migration_test_layer1', client)
        client_util.publish_map(username, 'migration_test_map1', client)

        run_statement(model.DROP_SCHEMA_SQL)

        ensure_schema()

        users = run_query(f'select count(*) from {DB_SCHEMA}.users;')
        assert users[0][0] == len(get_usernames())

        client_util.delete_layer(username, 'migration_test_layer1', client)
        client_util.delete_map(username, 'migration_test_map1', client)


def test_steps(client):
    username = 'migration_test_user2'
    with app.app_context():
        client_util.publish_layer(username, 'migration_test_layer2', client)
        client_util.publish_map(username, 'migration_test_map2', client)

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
        migrate_users_with_publications()
        exists_users = run_query(f'select count(*) from {DB_SCHEMA}.users;')
        assert exists_users[0][0] > 0

        client_util.delete_layer(username, 'migration_test_layer2', client)
        client_util.delete_map(username, 'migration_test_map2', client)
