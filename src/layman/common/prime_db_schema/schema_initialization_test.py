import logging

from test import process, process_client

from layman import settings, app as app, util
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE
from . import model, publications as pub_util, workspaces as workspaces_util
from .schema_initialization import migrate_users_and_publications, ensure_schema
from .util import run_query, run_statement


DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
ensure_layman = process.ensure_layman

logger = logging.getLogger(__name__)


def test_recreate_schema(ensure_layman):
    username = 'test_recreate_schema_user1'
    process_client.publish_layer(username, 'test_recreate_schema_layer1')
    process_client.publish_map(username, 'test_recreate_schema_map1')

    with app.app_context():
        run_statement(model.DROP_SCHEMA_SQL)
        ensure_schema(settings.LAYMAN_PRIME_SCHEMA,
                      settings.PUBLICATION_MODULES,
                      settings.RIGHTS_EVERYONE_ROLE)

    process_client.delete_layer(username, 'test_recreate_schema_layer1')
    process_client.delete_map(username, 'test_recreate_schema_map1')

    with app.app_context():
        pubs = pub_util.get_publication_infos(username)
        assert len(pubs) == 0


def test_schema(ensure_layman):
    username = 'migration_test_user1'
    layername = 'migration_test_layer1'
    mapname = 'migration_test_map1'
    process_client.publish_layer(username, layername)
    process_client.publish_map(username, mapname)

    with app.app_context():
        run_statement(model.DROP_SCHEMA_SQL)
        ensure_schema(settings.LAYMAN_PRIME_SCHEMA,
                      settings.PUBLICATION_MODULES,
                      settings.RIGHTS_EVERYONE_ROLE)

        workspaces = run_query(f'select count(*) from {DB_SCHEMA}.workspaces;')
        assert workspaces[0][0] == len(util.get_usernames())
        user_infos = workspaces_util.get_workspace_infos(username)
        assert username in user_infos
        pub_infos = pub_util.get_publication_infos(username)
        assert (username, layername, LAYER_TYPE) in pub_infos
        assert (username, mapname, MAP_TYPE) in pub_infos

    process_client.delete_layer(username, layername)
    process_client.delete_map(username, mapname)

    with app.app_context():
        pubs = pub_util.get_publication_infos(username)
        assert len(pubs) == 0


def test_steps(ensure_layman):
    username = 'migration_test_user2'
    process_client.publish_layer(username, 'migration_test_layer2')
    process_client.publish_map(username, 'migration_test_map2')

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

        exists_workspaces = run_query(f'select count(*) from {DB_SCHEMA}.workspaces;')
        assert exists_workspaces[0][0] == 0
        exists_pubs = run_query(f'select count(*) from {DB_SCHEMA}.publications;')
        assert exists_pubs[0][0] == 0
        migrate_users_and_publications(settings.PUBLICATION_MODULES, settings.RIGHTS_EVERYONE_ROLE)
        exists_workspaces = run_query(f'select count(*) from {DB_SCHEMA}.workspaces;')
        assert exists_workspaces[0][0] > 0
        exists_pubs = run_query(f'select count(*) from {DB_SCHEMA}.publications;')
        assert exists_pubs[0][0] > 0

    process_client.delete_layer(username, 'migration_test_layer2')
    process_client.delete_map(username, 'migration_test_map2')
