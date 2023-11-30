import logging

from db import util as db_util
from layman import settings

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
ROLE_SERVICE_SCHEMA = settings.LAYMAN_INTERNAL_ROLE_SERVICE_SCHEMA


def adjust_db_for_roles():
    logger.info(f'    Alter DB prime schema for roles')

    statement = f'''
ALTER TABLE {DB_SCHEMA}.rights ADD COLUMN IF NOT EXISTS
    role_name VARCHAR(64) COLLATE pg_catalog."default";

ALTER TABLE {DB_SCHEMA}.rights ALTER COLUMN id_user DROP NOT NULL;

ALTER TABLE {DB_SCHEMA}.rights ADD CONSTRAINT rights_role_xor_user
    CHECK ((id_user IS NULL) != (role_name IS NULL));

ALTER TABLE {DB_SCHEMA}.rights DROP CONSTRAINT IF EXISTS rights_unique_key;
ALTER TABLE {DB_SCHEMA}.rights ADD CONSTRAINT rights_unique_key unique (id_user, role_name, id_publication, type);
    '''

    db_util.run_statement(statement)


def create_role_service_schema():
    logger.info(f'    Create internal role service schema')

    statement = f"""CREATE SCHEMA IF NOT EXISTS "{ROLE_SERVICE_SCHEMA}" AUTHORIZATION {settings.LAYMAN_PG_USER};"""
    db_util.run_statement(statement)
