from layman import settings
from layman.util import get_modules_from_names

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
RIGHT_WRITE = 'write'
RIGHT_READ = 'read'

BOOLEAN_TRUE = 'true'
BOOLEAN_FALSE = 'false'


EXISTS_SCHEMA_SQL = f"""select count(*)
    from information_schema.schemata
    where schema_name = '{DB_SCHEMA}'
      AND schema_owner = '{settings.LAYMAN_PG_USER}'"""


DROP_SCHEMA_SQL = f'''DROP SCHEMA IF EXISTS "{DB_SCHEMA}" CASCADE;
COMMIT;'''


def setup_codelists_data():
    sql = f"""insert into {DB_SCHEMA}.right_types (name) values ('{RIGHT_WRITE}');
insert into {DB_SCHEMA}.right_types (name) values ('{RIGHT_READ}');"""

    for publ_module in get_modules_from_names(settings.PUBLICATION_MODULES):
        for type_def in publ_module.PUBLICATION_TYPES.values():
            publ_type_name = type_def['type']
            sql = sql + f"""
insert into {DB_SCHEMA}.publication_types (name) values ('{publ_type_name}');"""
    return sql


CREATE_SCHEMA_SQL = f"""CREATE SCHEMA IF NOT EXISTS "{DB_SCHEMA}" AUTHORIZATION {settings.LAYMAN_PG_USER};

CREATE SEQUENCE {DB_SCHEMA}.publication_types_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;
ALTER SEQUENCE {DB_SCHEMA}.publication_types_id_seq
    OWNER TO {settings.LAYMAN_PG_USER};

CREATE SEQUENCE {DB_SCHEMA}.right_types_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;
ALTER SEQUENCE {DB_SCHEMA}.right_types_id_seq
    OWNER TO {settings.LAYMAN_PG_USER};

CREATE SEQUENCE {DB_SCHEMA}.publications_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;
ALTER SEQUENCE {DB_SCHEMA}.publications_id_seq
    OWNER TO {settings.LAYMAN_PG_USER};

CREATE SEQUENCE {DB_SCHEMA}.users_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;
ALTER SEQUENCE {DB_SCHEMA}.users_id_seq
    OWNER TO {settings.LAYMAN_PG_USER};

CREATE SEQUENCE {DB_SCHEMA}.workspaces_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;
ALTER SEQUENCE {DB_SCHEMA}.workspaces_id_seq
    OWNER TO {settings.LAYMAN_PG_USER};

CREATE SEQUENCE {DB_SCHEMA}.rights_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;
ALTER SEQUENCE {DB_SCHEMA}.rights_id_seq
    OWNER TO {settings.LAYMAN_PG_USER};

CREATE TABLE {DB_SCHEMA}.publication_types
(
    id integer NOT NULL DEFAULT nextval('{DB_SCHEMA}.publication_types_id_seq'::regclass),
    name VARCHAR(64) COLLATE pg_catalog."default" not null,
    CONSTRAINT publication_types_pkey PRIMARY KEY (id),
    CONSTRAINT publication_types_name_key UNIQUE (name)
)
TABLESPACE pg_default;

CREATE TABLE {DB_SCHEMA}.right_types
(
    id integer NOT NULL DEFAULT nextval('{DB_SCHEMA}.right_types_id_seq'::regclass),
    name VARCHAR(64) COLLATE pg_catalog."default" not null,
    CONSTRAINT right_types_pkey PRIMARY KEY (id),
    CONSTRAINT right_types_username_key UNIQUE (name)
)
TABLESPACE pg_default;

CREATE TABLE {DB_SCHEMA}.workspaces
(
    id integer NOT NULL DEFAULT nextval('{DB_SCHEMA}.workspaces_id_seq'::regclass),
    name VARCHAR(256) COLLATE pg_catalog."default",
    CONSTRAINT workspaces_pkey PRIMARY KEY (id),
    CONSTRAINT workspaces_name_key UNIQUE (name)
)
TABLESPACE pg_default;

CREATE TABLE {DB_SCHEMA}.users
(
    id integer NOT NULL DEFAULT nextval('{DB_SCHEMA}.users_id_seq'::regclass),
    id_workspace integer REFERENCES {DB_SCHEMA}.workspaces (id),
    preferred_username VARCHAR(256) COLLATE pg_catalog."default",
    given_name VARCHAR(256) COLLATE pg_catalog."default",
    family_name VARCHAR(256) COLLATE pg_catalog."default",
    middle_name VARCHAR(256) COLLATE pg_catalog."default",
    name VARCHAR(256) COLLATE pg_catalog."default",
    email VARCHAR(1024) COLLATE pg_catalog."default",
    issuer_id VARCHAR(256) COLLATE pg_catalog."default",
    sub VARCHAR(256) COLLATE pg_catalog."default",
    CONSTRAINT users_pkey PRIMARY KEY (id),
    CONSTRAINT users_workspace_key UNIQUE (id_workspace)
)
TABLESPACE pg_default;

CREATE TABLE {DB_SCHEMA}.publications
(
    id integer NOT NULL DEFAULT nextval('{DB_SCHEMA}.publications_id_seq'::regclass),
    id_workspace integer REFERENCES {DB_SCHEMA}.workspaces (id) not null,
    name VARCHAR(256) COLLATE pg_catalog."default" not null,
    title VARCHAR(256) COLLATE pg_catalog."default" not null,
    type VARCHAR(64) COLLATE pg_catalog."default" not null references {DB_SCHEMA}.publication_types (name),
    uuid uuid not null,
    everyone_can_read boolean not null,
    everyone_can_write boolean not null,
    constraint publications_pkey primary key (id),
    constraint publications_uuid_key unique (uuid),
    constraint publications_name_type_key unique (id_workspace, type, name)
)
TABLESPACE pg_default;

create table {DB_SCHEMA}.rights
(
    id integer NOT NULL DEFAULT nextval('{DB_SCHEMA}.rights_id_seq'::regclass),
    id_user integer NOT NULL REFERENCES {DB_SCHEMA}.users (id),
    id_publication integer NOT NULL REFERENCES {DB_SCHEMA}.publications (id),
    type varchar(64) COLLATE pg_catalog."default" not null references {DB_SCHEMA}.right_types (name),
    constraint rights_pkey primary key (id),
    constraint rights_unique_key unique (id_user, id_publication, type)
)
TABLESPACE pg_default;

commit;
"""
