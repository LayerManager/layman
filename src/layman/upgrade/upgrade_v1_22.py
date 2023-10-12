import json
import glob
import logging
import os

from db import util as db_util
from layman import settings
from layman.common.filesystem.util import get_workspaces_dir
from layman.map import MAP_TYPE, util as map_util

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


def fix_issuer_id():
    logger.info(f'    Fix issuer_id in DB to correct value')

    query = f'''select distinct issuer_id from {DB_SCHEMA}.users;'''
    issuer_id_rows = db_util.run_query(query)
    found_issuer_ids = {row[0] for row in issuer_id_rows}
    known_issuer_ids = {'layman.authn.oauth2.liferay', 'layman.authn.oauth2'}
    unknown_issuer_ids = found_issuer_ids - known_issuer_ids
    assert len(unknown_issuer_ids) == 0, f"Unknown value(s) of issuer_id found: {unknown_issuer_ids}"

    statement = f'''update {DB_SCHEMA}.users set issuer_id = 'layman.authn.oauth2';'''
    db_util.run_statement(statement)


def remove_authn_txt_files():
    logger.info(f'    Remove authn.txt files')

    auth_paths = glob.glob(f"{get_workspaces_dir()}/*/authn.txt")
    logger.info(f'      Found {len(auth_paths)} authn.txt files to remove')

    for authn_path in auth_paths:
        os.remove(authn_path)
        logger.info(f'      File {authn_path} removed')


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


def insert_map_layer_relations():
    logger.info(f'    Insert map-layer relations')

    query = f'''
    select p.id, w.name, p.name
    from {DB_SCHEMA}.publications p inner join
         {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
    where p.type = %s
    ;'''
    maps = db_util.run_query(query, (MAP_TYPE, ))

    for map_id, workspace, map_name in maps:
        logger.info(f'        Import map-layer relations for map {workspace}.{map_name}')
        map_file_path = os.path.join(settings.LAYMAN_DATA_DIR, 'workspaces', workspace, 'maps', map_name, 'input_file', map_name + '.json')
        try:
            with open(map_file_path, 'r', encoding="utf-8") as map_file:
                map_json = json.load(map_file)

            map_layers = map_util.get_layers_from_json(map_json)
        except FileNotFoundError:
            logger.warning(f'File not found for map {workspace}.{map_name}, map file path {map_file_path}')
            map_layers = []
        for layer_workspace, layer_name, layer_index in map_layers:
            insert_query = f'''
            insert into {DB_SCHEMA}.map_layer(id_map, layer_workspace, layer_name, layer_index) values (%s, %s, %s, %s);
            '''
            db_util.run_statement(insert_query, (map_id, layer_workspace, layer_name, layer_index, ))
        logger.info(f'          Number of imported relations: {len(map_layers)}')
