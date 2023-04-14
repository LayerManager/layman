import pytest

from db import util as db_util
from layman import app, settings
from test_tools import process_client
from . import upgrade_v1_21

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


@pytest.mark.usefixtures('ensure_layman')
def test_wfs_wms_status():
    main_workspace = 'test_wfs_wms_status_workspace'

    layer_def = (main_workspace, process_client.LAYER_TYPE, 'test_layer', {})
    map_def = (main_workspace, process_client.MAP_TYPE, 'test_map', {})

    publication_defs = [layer_def, map_def, ]

    for workspace, publication_type, publication, rest_args in publication_defs:
        process_client.publish_workspace_publication(publication_type, workspace, publication, **rest_args)

    statement = f'''ALTER TABLE {DB_SCHEMA}.publications DROP COLUMN wfs_wms_status;'''
    with app.app_context():
        db_util.run_statement(statement)

        upgrade_v1_21.adjust_db_for_wfs_wms_status()
        upgrade_v1_21.adjust_publications_wfs_wms_status()

    query = f'''select p.wfs_wms_status
    from {DB_SCHEMA}.publications p left join
     {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
where w.name = %s
  and p.name = %s
  and p.type = %s
;'''
    for workspace, publication_type, publication, _ in publication_defs:
        with app.app_context():
            wfs_wms_status = db_util.run_query(query, (workspace, publication, publication_type))[0][0]
        if publication_type == process_client.LAYER_TYPE:
            assert wfs_wms_status == settings.EnumWfsWmsStatus.AVAILABLE.value, f'publication={publication_type}:{workspace}.{publication}, wfs_wms_status={wfs_wms_status}'
        else:
            assert wfs_wms_status is None, f'publication={publication_type}:{workspace}.{publication}, wfs_wms_status={wfs_wms_status}'
