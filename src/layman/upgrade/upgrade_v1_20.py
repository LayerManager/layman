import logging

from db import util as db_util
from layman import settings

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def adjust_db_for_table_uri():
    logger.info(f'    Alter DB prime schema for external_table_uri')

    statement = f'''
    CREATE EXTENSION IF NOT EXISTS pgcrypto;

    ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS external_table_uri bytea;'''
    db_util.run_statement(statement)

    statement = f'alter table {DB_SCHEMA}.publications add constraint external_table_uri_with_file_type_check CHECK ' \
                f'(external_table_uri IS NULL OR file_type = %s);'
    db_util.run_statement(statement, (settings.GEODATA_TYPE_VECTOR,))


def rename_file_type_to_geodata_type():
    logger.info(f'    Rename column file_type to geodata_type in DB prime schema')

    statement = f'''alter table {DB_SCHEMA}.publications rename column file_type to geodata_type;'''
    db_util.run_statement(statement)
