import logging

from db import util as db_util
from layman import settings

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def adjust_db_for_db_connection():
    logger.info(f'    Alter DB prime schema for db_connection')

    statement = f'''
    ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS db_connection json;'''
    db_util.run_statement(statement)

    statement = f'alter table {DB_SCHEMA}.publications add constraint db_connection_with_publ_type_check CHECK ' \
                f'(db_connection IS NULL OR file_type = %s);'
    db_util.run_statement(statement, (settings.FILE_TYPE_VECTOR, ))
