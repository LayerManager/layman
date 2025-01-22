import logging

from db import util as db_util
from layman import settings

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def ensure_issuer_sub_uniqueness():
    logger.info(f'    Ensure (issuer_id, sub) is unique for all users')

    statement = f'''
alter table {DB_SCHEMA}.users
    drop constraint users_sub_key;

alter table {DB_SCHEMA}.users
    add constraint users_issuer_sub_key
        unique (issuer_id, sub);'''

    db_util.run_statement(statement)


def create_map_layer_relation_table():
    logger.info(f'    Create map-layer relation table')

    sql_create_table = f'''
CREATE SEQUENCE {DB_SCHEMA}.map_layer_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;
ALTER SEQUENCE {DB_SCHEMA}.map_layer_id_seq
    OWNER TO {settings.LAYMAN_PG_USER};

CREATE TABLE {DB_SCHEMA}.map_layer
(
    id integer NOT NULL DEFAULT nextval('{DB_SCHEMA}.map_layer_id_seq'::regclass) PRIMARY KEY,
    id_map integer not null REFERENCES {DB_SCHEMA}.publications (id),
    layer_workspace VARCHAR(256) COLLATE pg_catalog."default" not null,
    layer_name VARCHAR(256) COLLATE pg_catalog."default" not null,
    layer_index integer NOT NULL,
    CONSTRAINT map_layer_unique_row UNIQUE (id_map, layer_workspace, layer_name, layer_index)
)
TABLESPACE pg_default;'''
    db_util.run_statement(sql_create_table)
