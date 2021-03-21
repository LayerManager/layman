import logging
from test import process_client
import pytest

from layman import settings, app, util, upgrade
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE
from . import model, publications as pub_util, workspaces as workspaces_util
from .schema_initialization import ensure_schema
from .util import run_query, run_statement


DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
username = 'test_schema_user'
layername = 'test_schema_layer'
mapname = 'test_schema_map'

logger = logging.getLogger(__name__)


@pytest.fixture()
def save_upgrade_status():
    with app.app_context():
        current_version = upgrade.get_current_data_version()
    yield
    with app.app_context():
        upgrade.upgrade_v1_9.initialize_data_versioning()
        upgrade.upgrade_v1_10.alter_schema()
        upgrade.upgrade_v1_10.update_style_type_in_db()
        upgrade.upgrade_v1_12.adjust_prime_db_schema_for_fulltext_search()
        upgrade.upgrade_v1_12.adjust_prime_db_schema_for_last_change_search()

        upgrade.set_current_data_version(current_version)


@pytest.fixture()
def prepare_publications():
    process_client.publish_workspace_layer(username, layername)
    process_client.publish_workspace_map(username, mapname)
    yield
    process_client.delete_workspace_layer(username, layername)
    process_client.delete_workspace_map(username, mapname)

    with app.app_context():
        pubs = pub_util.get_publication_infos(username)
        assert len(pubs) == 0


@pytest.mark.timeout(40)
@pytest.mark.usefixtures('ensure_layman', 'prepare_publications', 'save_upgrade_status')
def test_schema():
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
        select_publications = f"""with const as (select %s workspace_name)
select w.name as workspace_name,
       p.type,
       p.name
from const c inner join
     {DB_SCHEMA}.workspaces w on w.name = c.workspace_name inner join
     {DB_SCHEMA}.publications p on p.id_workspace = w.id left join
     {DB_SCHEMA}.users u on u.id_workspace = w.id
;"""
        pub_infos = run_query(select_publications, (username, ))
        assert (username, LAYER_TYPE, layername) in pub_infos
        assert (username, MAP_TYPE, mapname) in pub_infos
