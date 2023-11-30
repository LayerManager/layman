import logging

from db import util as db_util
from layman import settings
from layman.authz import role_service as role_service_util

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

    create_schema = f"""CREATE SCHEMA IF NOT EXISTS "{ROLE_SERVICE_SCHEMA}" AUTHORIZATION {settings.LAYMAN_PG_USER};"""
    db_util.run_statement(create_schema)

    create_role_table = f"""create table {ROLE_SERVICE_SCHEMA}.bussiness_roles(
    id integer GENERATED ALWAYS AS IDENTITY,
    name varchar(64) not null,
    parent varchar(64) references {ROLE_SERVICE_SCHEMA}.bussiness_roles (name),
    CONSTRAINT bussiness_roles_pkey PRIMARY KEY (id),
    CONSTRAINT bussiness_roles_name_key UNIQUE (name)
);"""
    db_util.run_statement(create_role_table)

    create_role_table = f"""create table {ROLE_SERVICE_SCHEMA}.bussiness_user_roles(
    id integer GENERATED ALWAYS AS IDENTITY,
    username varchar(128) not null references {DB_SCHEMA}.workspaces (name),
    rolename varchar(64) not null references {ROLE_SERVICE_SCHEMA}.bussiness_roles (name),
    CONSTRAINT bussiness_user_roles_pkey PRIMARY KEY (id),
    CONSTRAINT bussiness_user_roles_username_rolename_key UNIQUE (username,rolename)
);"""
    db_util.run_statement(create_role_table)

    create_layman_users_roles_view = f"""create view {ROLE_SERVICE_SCHEMA}.layman_users_roles
as
select concat('USER_', UPPER(w.name)) as name
from {DB_SCHEMA}.users u inner join
     {DB_SCHEMA}.workspaces w on w.id = u.id_workspace
;"""
    db_util.run_statement(create_layman_users_roles_view)

    create_layman_users_user_roles_view = f"""create view {ROLE_SERVICE_SCHEMA}.layman_users_user_roles
as
select w.name as username,
       concat('USER_', UPPER(w.name)) as rolename
from {DB_SCHEMA}.users u inner join
     {DB_SCHEMA}.workspaces w on w.id = u.id_workspace
;"""
    db_util.run_statement(create_layman_users_user_roles_view)

    role_service_util.ensure_admin_roles()
