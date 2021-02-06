import logging
import pytest

from test import process_client

from layman import settings, app, util, upgrade
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE
from layman.upgrade import upgrade_v1_9
from . import model, publications as pub_util, workspaces as workspaces_util
from .schema_initialization import ensure_schema
from .util import run_query, run_statement


DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA

logger = logging.getLogger(__name__)


@pytest.fixture()
def save_upgrade_status():
    with app.app_context():
        current_version = upgrade.get_current_data_version()
    yield
    with app.app_context():
        upgrade_v1_9.initialize_data_versioning()
        upgrade.set_current_data_version(current_version)


@pytest.mark.timeout(40)
@pytest.mark.usefixtures('ensure_layman', 'save_upgrade_status')
def test_schema():
    username = 'test_schema_user'
    layername = 'test_schema_layer'
    mapname = 'test_schema_map'
    process_client.publish_layer(username, layername)
    process_client.publish_map(username, mapname)

    with app.app_context():
        run_statement(model.DROP_SCHEMA_SQL)
        ensure_schema(settings.LAYMAN_PRIME_SCHEMA,
                      settings.RIGHTS_EVERYONE_ROLE)

        workspaces = run_query(f'select count(*) from {DB_SCHEMA}.workspaces;')
        assert workspaces[0][0] == len(util.get_workspaces())
        users = run_query(f'select count(*) from {DB_SCHEMA}.users;')
        assert users[0][0] == len(util.get_usernames(use_cache=False))
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
