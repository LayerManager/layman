import logging
from test_tools import process_client
import pytest

from db.util import run_query, run_statement
from layman import settings, app, util, upgrade
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE
from . import model, publications as pub_util, workspaces as workspaces_util
from .schema_initialization import ensure_schema


DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
USERNAME = 'test_schema_user'
LAYERNAME = 'test_schema_layer'
MAPNAME = 'test_schema_map'

logger = logging.getLogger(__name__)


@pytest.fixture()
def save_upgrade_status():
    with app.app_context():
        current_versions = {(migration_type, upgrade.get_current_version(migration_type))
                            for migration_type in [upgrade.consts.MIGRATION_TYPE_SCHEMA, upgrade.consts.MIGRATION_TYPE_DATA]}
    yield
    with app.app_context():
        upgrade.upgrade_v1_9.initialize_data_versioning()
        upgrade.upgrade_v1_10.alter_schema()
        upgrade.upgrade_v1_10.update_style_type_in_db()
        upgrade.upgrade_v1_12.adjust_db_for_schema_migrations()
        upgrade.upgrade_v1_12.adjust_prime_db_schema_for_fulltext_search()
        upgrade.upgrade_v1_12.adjust_prime_db_schema_for_last_change_search()
        upgrade.upgrade_v1_12.adjust_prime_db_schema_for_bbox_search()
        upgrade.upgrade_v1_12.adjust_data_for_last_change_search()

        for (migration_type, version) in current_versions:
            upgrade.set_current_migration_version(migration_type, version)


@pytest.fixture()
def prepare_publications():
    process_client.publish_workspace_layer(USERNAME, LAYERNAME)
    process_client.publish_workspace_map(USERNAME, MAPNAME)
    yield
    process_client.delete_workspace_layer(USERNAME, LAYERNAME)
    process_client.delete_workspace_map(USERNAME, MAPNAME)

    with app.app_context():
        pubs = pub_util.get_publication_infos(USERNAME)
        assert len(pubs) == 0


@pytest.mark.timeout(40)
@pytest.mark.usefixtures('ensure_layman', 'prepare_publications', 'save_upgrade_status')
def test_schema():
    with app.app_context():
        run_statement(model.DROP_SCHEMA_SQL)
        ensure_schema(settings.LAYMAN_PRIME_SCHEMA,)

        workspaces = run_query(f'select count(*) from {DB_SCHEMA}.workspaces;')
        assert workspaces[0][0] == len(util.get_workspaces())
        users = run_query(f'select count(*) from {DB_SCHEMA}.users;')
        assert users[0][0] == len(util.get_usernames(use_cache=False))
        user_infos = workspaces_util.get_workspace_infos(USERNAME)
        assert USERNAME in user_infos
        select_publications = f"""with const as (select %s workspace_name)
select w.name as workspace_name,
       p.type,
       p.name
from const c inner join
     {DB_SCHEMA}.workspaces w on w.name = c.workspace_name inner join
     {DB_SCHEMA}.publications p on p.id_workspace = w.id left join
     {DB_SCHEMA}.users u on u.id_workspace = w.id
;"""
        pub_infos = run_query(select_publications, (USERNAME,))
        assert (USERNAME, LAYER_TYPE, LAYERNAME) in pub_infos
        assert (USERNAME, MAP_TYPE, MAPNAME) in pub_infos
