import logging

from db import util as db_util
from layman import settings

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def adjust_db_for_image_mosaic():
    logger.info(f'    Alter DB prime schema for image_mosaic')

    statement = f'''
    ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS
    image_mosaic boolean not null default False;'''
    db_util.run_statement(statement)

    statement = f'alter table {DB_SCHEMA}.publications add constraint image_mosaic_with_publ_type_check CHECK ' \
                f'(file_type IN (%s, %s) or image_mosaic IS FALSE);'
    db_util.run_statement(statement, (settings.GEODATA_TYPE_RASTER, settings.GEODATA_TYPE_UNKNOWN))
