import logging
import shutil
from urllib.parse import urljoin
import requests
from psycopg2 import sql

from db import util as db_util
from geoserver import util as gs_util
from layman import settings, names
from layman.common.micka import util as micka_util, requests as micka_requests
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE
from layman.map.filesystem import input_file
from layman.util import get_publication_info

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def adjust_db_for_description():
    logger.info(f'    Alter DB prime schema for description')

    statement = f'''
    ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS
    description varchar(1024) default null;'''
    db_util.run_statement(statement)


def get_wms_capabilities(geoserver_workspace):
    headers = {
        settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE: settings.LAYMAN_GS_USER,
    }
    wms_url = urljoin(settings.LAYMAN_GS_URL, geoserver_workspace + '/ows')
    return gs_util.wms_direct(wms_url, headers=headers)


def adjust_publications_description():
    logger.info(f'    Adjust description of publications')
    query = f'''select w.name, p.type, p.name
    from {DB_SCHEMA}.publications p inner join
         {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
    where p.type = %s
       or p.wfs_wms_status = %s
    ;'''
    publications = db_util.run_query(query, (MAP_TYPE, settings.EnumWfsWmsStatus.AVAILABLE.value, ))

    for workspace, publ_type, publication in publications:
        logger.info(f'    Adjust description of {publ_type} {workspace}.{publication}')
        try:
            if publ_type == LAYER_TYPE:
                wms = get_wms_capabilities(geoserver_workspace=f'{workspace}_wms')
                description = wms.contents[publication].abstract
            else:
                description = input_file.get_map_info(workspace, publication)['description']
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout, requests.exceptions.HTTPError):
            description = None

        query = f'''update {DB_SCHEMA}.publications set
        description = %s
        where type = %s
          and name = %s
          and id_workspace = (select w.id from {DB_SCHEMA}.workspaces w where w.name = %s);'''
        params = (description, publ_type, publication, workspace,)
        db_util.run_statement(query, params)

    logger.info(f'    Adjusting publications description DONE')


def ensure_gs_workspaces():
    logger.info(f'    Ensure GS workspaces')
    all_gs_workspaces = gs_util.get_all_workspaces(auth=settings.LAYMAN_GS_AUTH)
    assert names.GEOSERVER_WFS_WORKSPACE not in all_gs_workspaces
    assert names.GEOSERVER_WMS_WORKSPACE not in all_gs_workspaces
    gs_util.ensure_workspace(names.GEOSERVER_WFS_WORKSPACE, auth=settings.LAYMAN_GS_AUTH)
    gs_util.ensure_workspace(names.GEOSERVER_WMS_WORKSPACE, auth=settings.LAYMAN_GS_AUTH)


def delete_layers_without_wfs_wms_available():
    logger.info(f'    Delete layers that do not have WFS/WMS available')

    query = f'''select w.name, p.name, p.uuid::varchar as uuid, p.id
    from {DB_SCHEMA}.publications p inner join
         {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
    where p.type = %s and p.wfs_wms_status != %s
    ;'''
    layers = db_util.run_query(query, (LAYER_TYPE, settings.EnumWfsWmsStatus.AVAILABLE.value, ))

    for workspace, layername, layer_uuid, layer_id in layers:
        logger.info(f'    Delete layer {workspace}.{layername}')

        # micka
        muuid = micka_util.get_metadata_uuid(layer_uuid)
        micka_requests.csw_delete(muuid)

        # geoserver sld
        gs_wms_workspace = f"{workspace}_wms"
        gs_util.delete_workspace_style(gs_wms_workspace, layername, auth=settings.LAYMAN_GS_AUTH)

        # geoserver wms
        gs_util.delete_feature_type(gs_wms_workspace, layername, settings.LAYMAN_GS_AUTH, store='postgresql')
        gs_util.delete_feature_type(gs_wms_workspace, layername, settings.LAYMAN_GS_AUTH, store=f'external_db_{layername}')
        gs_util.delete_wms_layer(gs_wms_workspace, layername, settings.LAYMAN_GS_AUTH)
        gs_util.delete_wms_store(gs_wms_workspace, settings.LAYMAN_GS_AUTH, f"qgis_{layername}")
        gs_util.delete_coverage_store(gs_wms_workspace, settings.LAYMAN_GS_AUTH, f"geotiff_{layername}")
        gs_util.delete_coverage_store(gs_wms_workspace, settings.LAYMAN_GS_AUTH, f"image_mosaic_{layername}")
        gs_util.delete_db_store(gs_wms_workspace, settings.LAYMAN_GS_AUTH, store_name=f"external_db_{layername}")
        gs_util.delete_security_roles(f"{gs_wms_workspace}.{layername}.r", settings.LAYMAN_GS_AUTH)
        gs_util.delete_security_roles(f"{gs_wms_workspace}.{layername}.w", settings.LAYMAN_GS_AUTH)

        # geoserver wfs
        gs_util.delete_feature_type(workspace, layername, settings.LAYMAN_GS_AUTH, store='postgresql')
        gs_util.delete_feature_type(workspace, layername, settings.LAYMAN_GS_AUTH, store=f'external_db_{layername}')
        gs_util.delete_db_store(workspace, settings.LAYMAN_GS_AUTH, store_name=f'external_db_{layername}')
        gs_util.delete_security_roles(f"{workspace}.{layername}.r", settings.LAYMAN_GS_AUTH)
        gs_util.delete_security_roles(f"{workspace}.{layername}.w", settings.LAYMAN_GS_AUTH)

        # qgis
        try:
            shutil.rmtree(f"{settings.LAYMAN_QGIS_DATA_DIR}/workspaces/{workspace}/layers/{layername}")
        except FileNotFoundError:
            pass

        # db
        table_name = f"layer_{layer_uuid.replace('-', '_')}"
        query = sql.SQL("""
        DROP TABLE IF EXISTS {table} CASCADE
        """).format(
            table=sql.Identifier(workspace, table_name),
        )
        db_util.run_statement(query)

        # primedbschema
        query = f"""with const as (select %s as name)
        select w.id,
               w.name
        from {DB_SCHEMA}.workspaces w inner join
             const c on (   c.name = w.name
                         or c.name is null)
        order by w.name asc
        ;"""
        values = db_util.run_query(query, (workspace,))
        if len(values) > 0:
            assert len(values) == 1
            workspace_id = values[0][0]

            query = f'''delete from {DB_SCHEMA}.rights where id_publication = %s;'''
            db_util.run_statement(query, (layer_id,))

            query = f"""delete from {DB_SCHEMA}.publications p where p.id_workspace = %s and p.name = %s and p.type = %s;"""
            db_util.run_statement(query, (workspace_id, layername, LAYER_TYPE,))

        # filesystem.uuid (Redis)
        # In upgrade process, UUIDs are not imported to Redis, so no need to delete it. Plus Redis is not persistent.

        # filesystem
        try:
            shutil.rmtree(f"{settings.LAYMAN_DATA_DIR}/workspaces/{workspace}/layers/{layername}")
        except FileNotFoundError:
            pass
        try:
            shutil.rmtree(f"{settings.LAYMAN_NORMALIZED_RASTER_DATA_DIR}/workspaces/{workspace}/layers/{layername}")
        except FileNotFoundError:
            pass

        # layman.celery.delete_publication (Redis)
        # In upgrade process, there is probably no information about async tasks. Plus Redis is not persistent.

        # far from perfect, but at least some assert that layer was deleted
        publ_info = get_publication_info(workspace, LAYER_TYPE, layername)
        assert not publ_info, f"{publ_info}"

        logger.info(f'    Deleting layer {workspace}.{layername} DONE!')
