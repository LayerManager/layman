import logging

from db import util as db_util
from layman import settings

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA

JSON_EXTENT_CRS = 'EPSG:4326'


def adjust_db_for_srid():
    logger.info(f'    Alter DB prime schema for native EPSG')

    statement = f'ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS srid integer;'
    db_util.run_statement(statement)


def adjust_db_publication_srid_constraint():
    statement = f'alter table {DB_SCHEMA}.publications add constraint bbox_with_crs_check CHECK ' \
                f'(bbox is null or srid is not null);'
    db_util.run_statement(statement)
