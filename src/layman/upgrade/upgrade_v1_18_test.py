import pytest

from db import util as db_util
from layman import app, settings
from test_tools import process_client
from . import upgrade_v1_18

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


@pytest.mark.usefixtures('ensure_layman')
def test_image_mosaic():
    main_workspace = 'test_image_mosaic_migration_workspace'

    layer_def = (main_workspace, process_client.LAYER_TYPE, 'test_layer')
    map_def = (main_workspace, process_client.MAP_TYPE, 'test_map')

    publication_defs = [layer_def, map_def, ]

    for workspace, publication_type, publication in publication_defs:
        process_client.publish_workspace_publication(publication_type, workspace, publication)

    # put DB to v1.17 state
    query = f'''
    ALTER TABLE {DB_SCHEMA}.publications DROP CONSTRAINT if exists image_mosaic_with_publ_type_check;
    ALTER TABLE {DB_SCHEMA}.publications DROP COLUMN image_mosaic;
    '''
    with app.app_context():
        db_util.run_statement(query)

    # assert DB is in 1.17 state
    query = f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='{DB_SCHEMA}' and table_name='publications' and column_name='image_mosaic';
    """
    with app.app_context():
        result = db_util.run_query(query)
    assert len(result) == 0

    # migrate to v1.18
    with app.app_context():
        upgrade_v1_18.adjust_db_for_image_mosaic()

    query = f'''
    select p.image_mosaic
from {DB_SCHEMA}.publications p left join
     {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
where w.name = %s
  and p.name = %s
;
    '''
    with app.app_context():
        result = db_util.run_query(query, (main_workspace, layer_def[2]))
    assert result[0][0] is False, f'result={result}'

    with app.app_context():
        result = db_util.run_query(query, (main_workspace, map_def[2]))
    assert result[0][0] is False, f'result={result}'

    # clean data
    for workspace, publication_type, publication in publication_defs:
        process_client.delete_workspace_publication(publication_type, workspace, publication)
