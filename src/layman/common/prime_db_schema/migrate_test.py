import logging
import pytest

from test import process_client

from layman import settings, app as app, util
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE
from . import model, publications as pub_util, workspaces as workspaces_util
from .schema_initialization import migrate_users_and_publications, ensure_schema
from .util import run_query, run_statement


DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA

logger = logging.getLogger(__name__)


@pytest.mark.timeout(20)
@pytest.mark.usefixtures('ensure_layman')
def test_recreate_schema():
    username = 'test_recreate_schema_user'
    process_client.publish_layer(username, 'test_recreate_schema_layer')
    process_client.publish_map(username, 'test_recreate_schema_map')

    with app.app_context():
        run_statement(model.DROP_SCHEMA_SQL)
        ensure_schema(settings.LAYMAN_PRIME_SCHEMA,
                      settings.PUBLICATION_MODULES,
                      settings.RIGHTS_EVERYONE_ROLE)

    process_client.delete_layer(username, 'test_recreate_schema_layer')
    process_client.delete_map(username, 'test_recreate_schema_map')

    with app.app_context():
        pubs = pub_util.get_publication_infos(username)
        assert len(pubs) == 0


@pytest.mark.usefixtures('ensure_layman')
def test_schema():
    username = 'test_schema_user'
    layername = 'test_schema_layer'
    mapname = 'test_schema_map'
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
        assert (username, LAYER_TYPE, layername) in pub_infos
        assert (username, MAP_TYPE, mapname) in pub_infos

    process_client.delete_layer(username, layername)
    process_client.delete_map(username, mapname)

    with app.app_context():
        pubs = pub_util.get_publication_infos(username)
        assert len(pubs) == 0


@pytest.mark.usefixtures('ensure_layman')
def test_steps():
    username = 'test_steps_user'
    process_client.publish_layer(username, 'test_steps_layer')
    process_client.publish_map(username, 'test_steps_map')

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

    process_client.delete_layer(username, 'test_steps_layer')
    process_client.delete_map(username, 'test_steps_map')
