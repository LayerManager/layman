import logging

from db import util as db_util
from layman import settings
from layman.layer import LAYER_TYPE, util
from layman.map import MAP_TYPE

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def adjust_db_for_wfs_wms_status():
    logger.info(f'    Alter DB prime schema for wfs_wms_status')
    status_string = ", ".join([f"'{status.value}'" for status in settings.EnumWfsWmsStatus])

    statement = f'''
    DO $$ BEGIN
        CREATE TYPE {DB_SCHEMA}.enum_wfs_wms_status AS ENUM ({status_string});
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
        ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS
        wfs_wms_status {DB_SCHEMA}.enum_wfs_wms_status;'''

    db_util.run_statement(statement)


def adjust_publications_wfs_wms_status():
    logger.info(f'    Adjust wfs_wms_status of publications')

    query = f'''select w.name,
        p.name
    from {DB_SCHEMA}.publications p inner join
         {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
    where p.type = %s
    ;'''
    publications = db_util.run_query(query, (LAYER_TYPE, ))

    for workspace, publication_name in publications:
        util.set_wfs_wms_status_after_fail(workspace, publication_name, )

    statement = f'alter table {DB_SCHEMA}.publications add constraint wfs_wms_status_with_type_check CHECK ' \
                f'((wfs_wms_status IS NULL AND type = %s) OR (wfs_wms_status IS NOT NULL AND type = %s));'
    db_util.run_statement(statement, (MAP_TYPE, LAYER_TYPE,))
