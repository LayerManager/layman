import logging

from layman import settings
from layman.common.prime_db_schema import util as db_util
from . import consts

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def adjust_db_for_schema_migrations():
    logger.info(f'    Alter DB prime schema for schema migrations')

    add_type = f'''
    DO $$ BEGIN
        CREATE TYPE {DB_SCHEMA}.enum_migration_type AS ENUM ('{consts.MIGRATION_TYPE_DATA}', '{consts.MIGRATION_TYPE_SCHEMA}');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;'''
    db_util.run_statement(add_type)
    add_column = f'''ALTER TABLE {DB_SCHEMA}.data_version ADD COLUMN IF NOT EXISTS
        migration_type {DB_SCHEMA}.enum_migration_type UNIQUE;'''
    db_util.run_statement(add_column)
    update_data = f'''update {DB_SCHEMA}.data_version set migration_type = '{consts.MIGRATION_TYPE_SCHEMA}';'''
    db_util.run_statement(update_data)
    insert_schema = f'''insert into {DB_SCHEMA}.data_version (major_version, minor_version, patch_version, migration, migration_type)
    values (-1, -1, -1, -1, '{consts.MIGRATION_TYPE_DATA}')'''
    db_util.run_statement(insert_schema)
    statement = f'ALTER TABLE {DB_SCHEMA}.data_version ALTER COLUMN migration_type SET NOT NULL;'
    db_util.run_statement(statement)


def adjust_prime_db_schema_for_fulltext_search():
    logger.info(f'    Alter DB prime schema for fulltext search')
    statement = f'''CREATE EXTENSION IF NOT EXISTS unaccent;
    drop index if exists {DB_SCHEMA}.title_tsv_idx;
    drop function if exists {DB_SCHEMA}.my_unaccent;

    CREATE FUNCTION {DB_SCHEMA}.my_unaccent(text) RETURNS tsvector LANGUAGE SQL IMMUTABLE AS 'SELECT to_tsvector(unaccent($1))';
    CREATE INDEX title_tsv_idx ON {DB_SCHEMA}.publications USING GIST ({DB_SCHEMA}.my_unaccent(title));
    '''

    db_util.run_statement(statement)


def adjust_prime_db_schema_for_last_change_search():
    logger.info(f'    Alter DB prime schema for search by updated_at')
    statement = f'ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone;'
    db_util.run_statement(statement)


def adjust_prime_db_schema_for_bbox_search():
    logger.info(f'    Alter DB prime schema for search by bbox')
    statement = f'ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS bbox box2d;'
    db_util.run_statement(statement)
