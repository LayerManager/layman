import datetime
import logging
import os
import time
import requests

from layman import settings
from layman.common.prime_db_schema import util as db_util
from layman.layer import LAYER_TYPE
from layman.layer.geoserver import wms
from layman.layer.micka import csw as layer_csw
from layman.map import MAP_TYPE
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


def adjust_data_for_last_change_search():
    logger.info(f'    Starting - Set updated_at for all publications')
    query = f'''select p.id,
       w.name,
       p.type,
       p.name
from {DB_SCHEMA}.publications p inner join
     {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
;'''
    publications = db_util.run_query(query)
    for (id, workspace, type, name, ) in publications:
        publ_dir = os.path.join(
            settings.LAYMAN_DATA_DIR,
            'users',
            workspace,
            type.split('.')[1] + 's',
            name,
        )
        updated_at = None
        for root, _, files in os.walk(publ_dir):
            for file in files:
                file_updated_at = os.stat(os.path.join(root, file)).st_mtime
                updated_at = max(updated_at, file_updated_at) if updated_at else file_updated_at
        updated_at = datetime.datetime.fromtimestamp(updated_at, datetime.timezone.utc)\
            if updated_at else datetime.datetime.now(datetime.timezone.utc)

        update = f'update {DB_SCHEMA}.publications set updated_at = %s where id = %s;'
        db_util.run_statement(update, (updated_at, id, ))

    statement = f'ALTER TABLE {DB_SCHEMA}.publications ALTER COLUMN updated_at SET NOT NULL;'
    db_util.run_statement(statement)
    logger.info(f'    DONE - Set updated_at for all publications')


def migrate_layer_metadata(workspace_filter=None):
    logger.info(f'    Starting - migrate layer metadata records')
    query = f'''
    select  w.name,
            p.name
    from {DB_SCHEMA}.publications p inner join
         {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
    where p.type = %s
    '''
    params = (LAYER_TYPE,)
    if workspace_filter:
        query = query + '  AND w.name = %s'
        params = params + (workspace_filter,)
    publications = db_util.run_query(query, params)
    for (workspace, layer) in publications:
        logger.info(f'      Migrate layer {workspace}.{layer}')
        try:
            muuid = layer_csw.patch_layer(workspace, layer, ['wms_url', 'wfs_url'],
                                          create_if_not_exists=False, timeout=2)
            if not muuid:
                logger.warning(f'        Metadata record of layer was not migrated, because the record does not exist.')
        except requests.exceptions.ReadTimeout:
            md_props = list(layer_csw.get_metadata_comparison(workspace, layer).values())
            md_wms_url = md_props[0]['wms_url'] if md_props else None
            base_wms_url = wms.add_capabilities_params_to_url(wms.get_wms_url(workspace, external_url=True))
            exp_wms_url = f"{base_wms_url}?LAYERS={layer}"
            if md_wms_url != exp_wms_url:
                logger.exception(
                    f'        WMS URL was not migrated (should be {exp_wms_url}, but is {md_wms_url})!')
        time.sleep(0.5)

    logger.info(f'     DONE - migrate layer metadata records')


def adjust_prime_db_schema_for_bbox_search():
    logger.info(f'    Alter DB prime schema for search by bbox')
    statement = f'ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS bbox box2d;'
    db_util.run_statement(statement)


def adjust_data_for_bbox_search():
    logger.info(f'    Starting - Set bbox for all publications')

    query = f'''
    select  w.name,
            p.type,
            p.name
    from {DB_SCHEMA}.publications p inner join
         {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
    where p.type = %s
    '''
    params = (LAYER_TYPE,)
    publications = db_util.run_query(query, params)
    for (workspace, _, layer) in publications:
        logger.info(f'      Migrate layer {workspace}.{layer}')
        table_query = f'''
        SELECT count(*)
        FROM pg_tables
        WHERE schemaname = '{workspace}'
          AND tablename = '{layer}'
          AND tableowner = '{settings.LAYMAN_PG_USER}'
        ;'''
        cnt = db_util.run_query(table_query)[0][0]
        if cnt == 0:
            logger.warning(f'      Layer DB table not available, not migrating.')
            continue

        bbox_query = f'''
        select ST_Extent(l.wkb_geometry) bbox
        from {workspace}.{layer} l
        ;'''
        bbox = db_util.run_query(bbox_query)[0]
        set_layer_bbox_query = f'''
        update {DB_SCHEMA}.publications set
            bbox = %s
        where type = %s
          and name = %s
          and id_workspace = (select w.id from {DB_SCHEMA}.workspaces w where w.name = %s);'''
        db_util.run_statement(set_layer_bbox_query, (bbox, LAYER_TYPE, layer, workspace,))

    params = (MAP_TYPE,)
    publications = db_util.run_query(query, params)
    for (workspace, _, map) in publications:
        from layman.map.filesystem import input_file
        logger.info(f'      Migrate map {workspace}.{map}')
        map_json = input_file.get_map_json(workspace, map)
        bbox_4326 = float(map_json['extent'][0]), float(map_json['extent'][1]),\
            float(map_json['extent'][2]), float(map_json['extent'][3])
        query_transform = f'''
        with tmp as (select ST_Transform(ST_SetSRID(ST_MakeBox2D(ST_Point(%s, %s), ST_Point(%s, %s)), %s), %s) bbox)
        select st_xmin(bbox),
               st_ymin(bbox),
               st_xmax(bbox),
               st_ymax(bbox)
        from tmp
        ;'''
        params = bbox_4326 + (4326, 3857,)
        try:
            bbox_3857 = db_util.run_query(query_transform, params)[0]
        except BaseException:
            logger.warning(f'        Bounding box not transformed, so set to None.')
            bbox_3857 = (None, None, None, None)

        set_map_bbox_query = f'''
        update {DB_SCHEMA}.publications set
            bbox = ST_MakeBox2D(ST_Point(%s, %s), ST_Point(%s ,%s))
        where type = %s
          and name = %s
          and id_workspace = (select w.id from {DB_SCHEMA}.workspaces w where w.name = %s);'''
        params = bbox_3857 + (MAP_TYPE, map, workspace,)
        db_util.run_statement(set_map_bbox_query, params)

    logger.info(f'     DONE - Set bbox for all publications')
