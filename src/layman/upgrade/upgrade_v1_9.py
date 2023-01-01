import logging

from layman import settings
from layman.common.prime_db_schema import util as db_util

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA

logger = logging.getLogger(__name__)


def initialize_data_versioning():
    logger.info(f'    Starting - data versioning initialization')

    sql_create_table = f'''CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.data_version
    (
        major_version integer not null,
        minor_version integer not null,
        patch_version integer not null,
        migration integer not null
    )
    TABLESPACE pg_default;'''
    db_util.run_statement(sql_create_table)

    # This table should have only one row and now should have none, otherwise something is wrong.
    sql_select_count = f'''select count(*) from {DB_SCHEMA}.data_version'''
    row_count = db_util.run_query(sql_select_count)[0][0]
    assert row_count == 0

    # Set initialization value to 0
    sql_insert = f'''insert into {DB_SCHEMA}.data_version (major_version, minor_version, patch_version, migration) values (1, 9, 0, 0);'''
    db_util.run_statement(sql_insert)

    logger.info(f'    DONE - data versioning initialization')
