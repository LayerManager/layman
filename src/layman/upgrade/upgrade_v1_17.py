import logging

from db import util as db_util
from layman import settings
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def adjust_db_for_file_type():
    logger.info(f'    Alter DB prime schema for file type')

    statement = f'''
    DO $$ BEGIN
        CREATE TYPE {DB_SCHEMA}.enum_file_type AS ENUM ('vector', 'raster', 'unknown');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
        ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS
        file_type {DB_SCHEMA}.enum_file_type;'''

    db_util.run_statement(statement)


def adjust_db_publication_file_type_constraint():
    statement = f'alter table {DB_SCHEMA}.publications add constraint file_type_with_publ_type_check CHECK ' \
                f'((type = %s AND geodata_type IS NULL) OR (type = %s AND geodata_type IS NOT NULL));'
    db_util.run_statement(statement, (MAP_TYPE, LAYER_TYPE))
