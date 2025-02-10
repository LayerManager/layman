import logging
import shutil
from urllib.parse import urljoin
import requests
from psycopg2 import sql

from db import util as db_util
from geoserver import util as gs_util
from layman import settings, names
from layman.common.micka import util as micka_util, requests as micka_requests
from layman.layer import LAYER_TYPE, STYLE_TYPES_DEF
from layman.layer.geoserver import wfs, wms as gs_wms, sld
from layman.layer.geoserver.tasks import refresh_wms, refresh_wfs, refresh_sld
from layman.layer.geoserver.wms import get_timeregex_props
from layman.layer.util import get_complete_layer_info
from layman.map import MAP_TYPE
from layman.map.filesystem import input_file
from layman.upgrade import upgrade_v2_0_util as util
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

        # geoserver
        util.delete_layer_from_geoserver_v1_23(layername, workspace)

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


def migrate_layers():
    logger.info(f'    Migrate layers')

    query = f'''
    select w.name, p.name, p.uuid::varchar as uuid, p.style_type, p.title, p.description, p.image_mosaic,
        PGP_SYM_DECRYPT(p.external_table_uri, p.uuid::text)::json as external_table_uri,
       (select rtrim(concat(case when u.id is not null then w.name || ',' end,
                            string_agg(COALESCE(w2.name, r.role_name), ',' ORDER BY COALESCE(w2.name, r.role_name)) || ',',
                            case when p.everyone_can_read then 'EVERYONE' || ',' end
                            ), ',')
        from {DB_SCHEMA}.rights r left join
             {DB_SCHEMA}.users u2 on r.id_user = u2.id left join
             {DB_SCHEMA}.workspaces w2 on w2.id = u2.id_workspace
        where r.id_publication = p.id
          and r.type = 'read') read_users_roles,
       (select rtrim(concat(case when u.id is not null then w.name || ',' end,
                            string_agg(COALESCE(w2.name, r.role_name), ',' ORDER BY COALESCE(w2.name, r.role_name)) || ',',
                            case when p.everyone_can_write then 'EVERYONE' || ',' end
                            ), ',')
        from {DB_SCHEMA}.rights r left join
             {DB_SCHEMA}.users u2 on r.id_user = u2.id left join
             {DB_SCHEMA}.workspaces w2 on w2.id = u2.id_workspace
        where r.id_publication = p.id
          and r.type = 'write') write_users_roles
    from {DB_SCHEMA}.publications p inner join
         {DB_SCHEMA}.workspaces w on w.id = p.id_workspace left join
         {DB_SCHEMA}.users u on u.id_workspace = w.id
    where p.type = %s
    ;'''
    layers = db_util.run_query(query, (LAYER_TYPE,))

    for workspace, layername, layer_uuid, style_type_code, title, description, image_mosaic, external_table_uri, \
            read_users_roles, write_users_roles in layers:

        # check if publication is not yet migrated
        publ_info = get_complete_layer_info(workspace, layername)
        publ_status = publ_info['layman_metadata']['publication_status']
        assert publ_status in ['COMPLETE', 'INCOMPLETE']
        if publ_status == 'INCOMPLETE':
            logger.info(f'    Migrate layer {workspace}.{layername}')
        else:
            logger.warning(f'    Layer {workspace}.{layername} seems already migrated!')
            continue

        # prepare task arguments
        style_type = next(st for st in STYLE_TYPES_DEF if st.code == style_type_code)
        original_data_source = settings.EnumOriginalDataSource.TABLE.value if external_table_uri else settings.EnumOriginalDataSource.FILE.value
        access_rights = {
            'read': read_users_roles.split(','),
            'write': write_users_roles.split(','),
        }
        if image_mosaic:
            time_regex_props = get_timeregex_props(workspace, layername)
            slugified_time_regex = time_regex_props['regex']
            slugified_time_regex_format = time_regex_props.get('regex_format')
        else:
            slugified_time_regex = None
            slugified_time_regex_format = None
        post_task_kwargs = {
            'uuid': layer_uuid,
            'title': title,
            'description': description,
            'access_rights': access_rights,
            'original_data_source': original_data_source,
            'store_in_geoserver': style_type.store_in_geoserver,
            'image_mosaic': image_mosaic,
            'slugified_time_regex': slugified_time_regex,
            'slugified_time_regex_format': slugified_time_regex_format,
        }

        # delete layer from geoserver
        util.delete_layer_from_geoserver_v1_23(layername, workspace)

        # re-create layer on geoserver
        if not wfs.get_layer_info_by_uuid(uuid=layer_uuid, layman_workspace=workspace):
            logger.info("      re-creating geoserver.wfs")
            util.run_task_sync(refresh_wfs, [workspace, layername], post_task_kwargs)
        else:
            logger.warning("      geoserver.wfs already exists!")

        if not gs_wms.get_layer_info_by_uuid(uuid=layer_uuid, gdal_layername=layername, gdal_workspace=workspace):
            logger.info("      re-creating geoserver.wms")
            util.run_task_sync(refresh_wms, [workspace, layername], post_task_kwargs)
        else:
            logger.warning("      geoserver.wms already exists!")

        if not sld.get_layer_info_by_uuid(workspace, uuid=layer_uuid, layername=layername):
            logger.info("      re-creating geoserver.sld")
            util.run_task_sync(refresh_sld, [workspace, layername], post_task_kwargs)
        else:
            logger.warning("      geoserver.sld already exists!")

        # assert that layer is complete now
        publ_info = get_complete_layer_info(workspace, layername)
        publ_status = publ_info['layman_metadata']['publication_status']
        assert publ_status == 'COMPLETE'

        logger.info(f'    Migrate layer {workspace}.{layername} DONE')


def delete_old_workspaces():
    logger.info(f'    Delete old workspaces')

    query = f"""
    select w.name
    from {DB_SCHEMA}.workspaces w
    order by w.name asc
    ;"""
    rows = db_util.run_query(query)
    workspaces = [r[0] for r in rows]

    for workspace in workspaces:
        logger.info(f'      Deleting old workspace {workspace}')

        # geoserver
        for gs_workspace in [workspace, f"{workspace}_wms"]:
            gs_util.delete_db_store(gs_workspace, auth=settings.LAYMAN_GS_AUTH, store_name='postgresql')
            gs_util.delete_workspace(gs_workspace, auth=settings.LAYMAN_GS_AUTH)

    logger.info(f'    Delete old workspaces DONE!')
