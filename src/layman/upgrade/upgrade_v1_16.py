import logging

from db import util as db_util
from layman import settings

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def adjust_db_for_srid():
    logger.info(f'    Alter DB prime schema for native EPSG')

    statement = f'ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS srid integer;'
    db_util.run_statement(statement)
