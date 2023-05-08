import pytest

from db import util as db_util
from layman import app, settings
from test_tools import process_client
from . import upgrade_v1_21

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


@pytest.mark.parametrize('publ_type, publ_name, rest_args, exp_wfs_wms_status', [
    pytest.param(
        process_client.LAYER_TYPE,
        'test_layer',
        {},
        settings.EnumWfsWmsStatus.AVAILABLE,
        id='layer_available',
    ),
    pytest.param(
        process_client.LAYER_TYPE,
        'test_updating_layer',
        {
            'compress': True,
            'with_chunks': True,
            'do_not_upload_chunks': True,
        },
        settings.EnumWfsWmsStatus.NOT_AVAILABLE,
        id='layer_updating',
    ),
    pytest.param(
        process_client.LAYER_TYPE,
        'test_failed_layer',
        {
            'file_paths': [
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.cpg',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.dbf',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shx',
            ],
            'compress': True,
            'with_chunks': True,
        },
        settings.EnumWfsWmsStatus.NOT_AVAILABLE,
        id='layer_not_available',
    ),
    pytest.param(
        process_client.MAP_TYPE,
        'test_map',
        {},
        settings.EnumWfsWmsStatus.AVAILABLE,
        id='map',
    ),
])
@pytest.mark.usefixtures('ensure_layman')
def test_wfs_wms_status(publ_type, publ_name, rest_args, exp_wfs_wms_status):
    workspace = 'test_wfs_wms_status_workspace'

    process_client.publish_workspace_publication(publ_type, workspace, publ_name, **rest_args)

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
    with app.app_context():
        wfs_wms_status = db_util.run_query(query, (workspace, publ_name, publ_type))[0][0]
    if publ_type == process_client.LAYER_TYPE:
        assert wfs_wms_status == exp_wfs_wms_status.value, f'publication={publ_type}:{workspace}.{publ_name}, wfs_wms_status={wfs_wms_status}'
    else:
        assert wfs_wms_status is None, f'publication={publ_type}:{workspace}.{publ_name}, wfs_wms_status={wfs_wms_status}'

    process_client.delete_workspace_publication(publ_type, workspace, publ_name)
