import logging

from db import util as db_util
from layman import settings

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
