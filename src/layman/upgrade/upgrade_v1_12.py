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

logger = logging.getLogger(__name__)

db_schema = settings.LAYMAN_PRIME_SCHEMA


def adjust_prime_db_schema_for_fulltext_search():
    statement = f'''CREATE EXTENSION IF NOT EXISTS unaccent;
    drop index if exists {db_schema}.title_tsv_idx;
    drop function if exists {db_schema}.my_unaccent;

    CREATE FUNCTION {db_schema}.my_unaccent(text) RETURNS tsvector LANGUAGE SQL IMMUTABLE AS 'SELECT to_tsvector(unaccent($1))';
    CREATE INDEX title_tsv_idx ON {db_schema}.publications USING GIST ({db_schema}.my_unaccent(title));
    '''

    db_util.run_statement(statement)


def adjust_prime_db_schema_for_last_change_search():
    statement = f'ALTER TABLE {db_schema}.publications ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone;'
    db_util.run_statement(statement)

    query = f'''select p.id,
       w.name,
       p.type,
       p.name
from {db_schema}.publications p inner join
     {db_schema}.workspaces w on w.id = p.id_workspace
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

        update = f'update {db_schema}.publications set updated_at = %s where id = %s;'
        db_util.run_statement(update, (updated_at, id, ))

    statement = f'ALTER TABLE {db_schema}.publications ALTER COLUMN updated_at SET NOT NULL;'
    db_util.run_statement(statement)


def migrate_layer_metadata(workspace_filter=None):
    logger.info(f'    Starting - migrate layer metadata records')
    query = f'''
    select  w.name,
            p.name
    from {db_schema}.publications p inner join
         {db_schema}.workspaces w on w.id = p.id_workspace
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

    logger.info(f'    DONE - migrate layer metadata records')


def adjust_prime_db_schema_for_bbox_search():
    statement = f'ALTER TABLE {db_schema}.publications ADD COLUMN IF NOT EXISTS bbox box2d;'
    db_util.run_statement(statement)
