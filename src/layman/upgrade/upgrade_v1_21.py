import logging

from db import util as db_util
from layman import settings
from layman.layer import LAYER_TYPE
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
    statement = f'alter table {DB_SCHEMA}.publications add constraint wfs_wms_status_with_type_check CHECK ' \
                f'((wfs_wms_status IS NULL AND type = %s) OR (wfs_wms_status IS NOT NULL AND type = %s));'
    db_util.run_statement(statement, (MAP_TYPE, LAYER_TYPE,))


def ensure_sub_uniqueness():
    logger.info(f'    Ensure sub is unique for all users')

    statement = f'''
alter table {DB_SCHEMA}.users
    drop constraint users_issuer_sub_key;

alter table {DB_SCHEMA}.users
    add constraint users_sub_key
        unique (sub);'''

    db_util.run_statement(statement)
