import logging

from db import util as db_util
from layman import settings

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def adjust_db_for_table_uri():
    logger.info(f'    Alter DB prime schema for db_connection')

    statement = f'''
    ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS table_uri json;'''
    db_util.run_statement(statement)

    statement = f'alter table {DB_SCHEMA}.publications add constraint table_uri_with_file_type_check CHECK ' \
                f'(table_uri IS NULL OR file_type = %s);'
    db_util.run_statement(statement, (settings.FILE_TYPE_VECTOR, ))
