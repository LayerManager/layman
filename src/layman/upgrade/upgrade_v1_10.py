import logging

from layman import settings
from layman.common.prime_db_schema import util as db_util

logger = logging.getLogger(__name__)

db_schema = settings.LAYMAN_PRIME_SCHEMA


def alter_schema():
    logger.info(f'    Starting - alter DB prime schema')
    db_schema = settings.LAYMAN_PRIME_SCHEMA
    add_column = f'''
DO $$ BEGIN
    CREATE TYPE {db_schema}.enum_style_type AS ENUM ('sld', 'qml');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;
    ALTER TABLE {db_schema}.publications ADD COLUMN IF NOT EXISTS
    style_type {db_schema}.enum_style_type;'''
    db_util.run_statement(add_column)
    logger.info(f'    DONE - alter DB prime schema')


def update_style_type_in_db():
    logger.info(f'    Starting - fulfill style type column in DB')
    db_schema = settings.LAYMAN_PRIME_SCHEMA

    update_layers = f"""update {db_schema}.publications set style_type = 'sld' where type = 'layman.layer'"""
    db_util.run_statement(update_layers)
    add_constraint = f"""DO $$ BEGIN
    alter table {db_schema}.publications add constraint con_style_type
check (type = 'layman.map' or style_type is not null);
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;"""
    db_util.run_statement(add_constraint)

    logger.info(f'    DONE - fulfill style type column in DB')
