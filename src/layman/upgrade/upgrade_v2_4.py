import logging

from db import util as db_util
from layman import settings

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def adjust_db_for_file_path():
    logger.info(f'    Alter DB prime schema for file_path')

    statement = f'''
    ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS file_path text;'''
    db_util.run_statement(statement)

    statement = f'alter table {DB_SCHEMA}.publications add constraint file_path_with_geodata_type_check CHECK ' \
                f'(file_path IS NULL OR geodata_type = %s);'
    db_util.run_statement(statement, (settings.GEODATA_TYPE_RASTER,))
