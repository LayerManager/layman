import pytest

from db import util as db_util
from layman import app, settings
from test_tools import process_client
from . import upgrade_v1_20

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


@pytest.mark.usefixtures('ensure_layman')
def test_db_connection():
    main_workspace = 'test_db_connection_migration_workspace'

    layer_vector_def = (main_workspace, process_client.LAYER_TYPE, 'test_layer_vector', dict())
    layer_raster_def = (main_workspace, process_client.LAYER_TYPE, 'test_layer_raster', {'file_paths': ['sample/layman.layer/sample_jp2_rgb.jp2', ]})
    map_def = (main_workspace, process_client.MAP_TYPE, 'test_map', dict())

    publication_defs = [layer_vector_def, layer_raster_def, map_def, ]

    for workspace, publication_type, publication, rest_args in publication_defs:
        process_client.publish_workspace_publication(publication_type, workspace, publication, **rest_args)

    statement = f'''
    ALTER TABLE {DB_SCHEMA}.publications DROP COLUMN table_uri;'''
    with app.app_context():
        db_util.run_statement(statement)

        upgrade_v1_20.adjust_db_for_table_uri()

    query = f'''select p.table_uri, p.uuid
    from {DB_SCHEMA}.publications p left join
     {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
where w.name = %s
  and p.name = %s
  and p.type = %s
;'''
    for workspace, publication_type, publication, _ in publication_defs:
        with app.app_context():
            table_uri = db_util.run_query(query, (workspace, publication, publication_type))[0][0]
        assert not table_uri, f'publication={publication_type}:{workspace}.{publication}, table_uri={table_uri}'
