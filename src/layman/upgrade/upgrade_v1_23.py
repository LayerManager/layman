import logging

from geoserver import util as gs_util
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
    logger.info(f'    Complete internal role service schema')

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

    create_admin_roles_view = f"""CREATE view {ROLE_SERVICE_SCHEMA}.admin_roles
    as
    select 'ADMIN' as name
    UNION ALL
    select 'GROUP_ADMIN'
    UNION ALL
    select %s
    ;"""
    db_util.run_statement(create_admin_roles_view, (settings.LAYMAN_GS_ROLE, ))

    create_admin_user_roles_view = f"""CREATE view {ROLE_SERVICE_SCHEMA}.admin_user_roles
    as
    select %s as username, %s as rolename
    UNION ALL
    select %s, 'ADMIN'
    UNION ALL
    select %s, 'ADMIN'
    union all
    select w.name as username,
           %s as rolename
    from {settings.LAYMAN_PRIME_SCHEMA}.users u inner join
         {settings.LAYMAN_PRIME_SCHEMA}.workspaces w on w.id = u.id_workspace
    ;"""
    db_util.run_statement(create_admin_user_roles_view, (settings.LAYMAN_GS_USER, settings.LAYMAN_GS_ROLE, settings.LAYMAN_GS_USER, settings.GEOSERVER_ADMIN_USER, settings.LAYMAN_GS_ROLE, ))

    create_roles_view = f"""create or replace view {ROLE_SERVICE_SCHEMA}.roles
as
select name::varchar(64),
       parent::varchar(64)
from {ROLE_SERVICE_SCHEMA}.bussiness_roles
UNION ALL
select name,
       null
from {ROLE_SERVICE_SCHEMA}.layman_users_roles
UNION ALL
select name,
       null
from {ROLE_SERVICE_SCHEMA}.admin_roles
;"""
    db_util.run_statement(create_roles_view)

    create_user_roles_view = f"""create or replace view {ROLE_SERVICE_SCHEMA}.user_roles
as
select username::varchar(64),
       rolename::varchar(64)
from {ROLE_SERVICE_SCHEMA}.bussiness_user_roles
UNION ALL
select username,
       rolename
from {ROLE_SERVICE_SCHEMA}.layman_users_user_roles
UNION ALL
select username,
       rolename
from {ROLE_SERVICE_SCHEMA}.admin_user_roles
;"""
    db_util.run_statement(create_user_roles_view)

    gs_util.reload(settings.LAYMAN_GS_AUTH)


def restrict_workspace_name_length():
    logger.info(f'    Restrict workspace name length')

    select_too_long = f"""
select name
from {settings.LAYMAN_PRIME_SCHEMA}.workspaces
where length(name) > 59
;"""
    too_long_workspace_name = db_util.run_query(select_too_long)
    if len(too_long_workspace_name) > 0:
        raise NotImplementedError(f"Too long workspace names: {[name[0] for name in too_long_workspace_name]}")

    alter_column = f"""
ALTER TABLE {settings.LAYMAN_PRIME_SCHEMA}.workspaces
    ALTER COLUMN name TYPE VARCHAR(59) COLLATE pg_catalog."default"
;"""
    db_util.run_statement(alter_column)


def remove_right_types_table():
    logger.info(f'    Remove right_types table')

    remove_fk_statement = f"""alter table {settings.LAYMAN_PRIME_SCHEMA}.rights drop constraint rights_type_fkey;"""
    db_util.run_statement(remove_fk_statement)

    create_check_statement = f"""alter table {settings.LAYMAN_PRIME_SCHEMA}.rights add constraint rights_type check (type in ('read', 'write'));"""
    db_util.run_statement(create_check_statement)

    drop_table_statement = f"""drop table {settings.LAYMAN_PRIME_SCHEMA}.right_types"""
    db_util.run_statement(drop_table_statement)
