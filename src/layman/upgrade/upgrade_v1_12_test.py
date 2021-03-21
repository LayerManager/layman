import datetime
from test import process_client
import pytest

from layman import app, settings
from layman.common.prime_db_schema import util as db_util
from . import upgrade_v1_12

db_schema = settings.LAYMAN_PRIME_SCHEMA


@pytest.mark.usefixtures('ensure_layman')
def test_adjust_prime_db_schema_for_last_change_search():
    workspace = 'test_adjust_prime_db_schema_for_last_change_search_workspace'
    layer = 'test_adjust_prime_db_schema_for_last_change_search_layer'
    map = 'test_adjust_prime_db_schema_for_last_change_search_map'

    timestamp1 = datetime.datetime.now(datetime.timezone.utc)
    process_client.publish_workspace_layer(workspace, layer)
    process_client.publish_workspace_map(workspace, map)
    timestamp2 = datetime.datetime.now(datetime.timezone.utc)
    with app.app_context():
        statement = f'ALTER TABLE {db_schema}.publications ALTER COLUMN updated_at DROP NOT NULL;'
        db_util.run_statement(statement)
        statement = f'update {db_schema}.publications set updated_at = null;'
        db_util.run_statement(statement)

        query = f'select p.id from {db_schema}.publications p where p.updated_at is not null;'
        results = db_util.run_query(query)
        assert not results, results

        upgrade_v1_12.adjust_prime_db_schema_for_last_change_search()

        query = f'''
select p.updated_at
from {db_schema}.publications p inner join
     {db_schema}.workspaces w on p.id_workspace = w.id
where w.name = %s
  and p.type = %s
  and p.name = %s
;'''
        results = db_util.run_query(query, (workspace, 'layman.layer', layer))
        assert len(results) == 1 and len(results[0]) == 1, results
        layer_updated_at = results[0][0]
        assert timestamp1 < layer_updated_at < timestamp2

        results = db_util.run_query(query, (workspace, 'layman.map', map))
        assert len(results) == 1 and len(results[0]) == 1, results
        map_updated_at = results[0][0]
        assert timestamp1 < map_updated_at < timestamp2

        assert layer_updated_at < map_updated_at

    process_client.delete_workspace_layer(workspace, layer)
    process_client.delete_workspace_map(workspace, map)
