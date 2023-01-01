import logging

from layman import settings
from layman.common.prime_db_schema import util as db_util

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
    db_util.run_statement(statement, data=(settings.FILE_TYPE_RASTER, settings.FILE_TYPE_UNKNOWN))
