from datetime import datetime
import json
import logging
import os
import shutil
from urllib.parse import urljoin
import traceback
import requests
from psycopg2 import sql

from db import util as db_util
from geoserver import util as gs_util
from layman import settings, names
from layman.common.micka import util as micka_util, requests as micka_requests
from layman.layer import LAYER_TYPE, STYLE_TYPES_DEF, db as layer_db
from layman.layer.db import table as layer_db_table
from layman.layer.filesystem import input_file, util as layer_file_util, gdal
from layman.layer.geoserver import wfs, wms as gs_wms, sld
from layman.layer.geoserver.tasks import refresh_wms, refresh_wfs, refresh_sld
from layman.layer.geoserver.util import DEFAULT_INTERNAL_DB_STORE
from layman.layer.geoserver.wms import get_timeregex_props
from layman.layer.qgis.tasks import refresh_wms as qgis_refresh_wms
from layman.layer.util import get_complete_layer_info
from layman.map import MAP_TYPE
from layman.map.util import get_complete_map_info, get_layers_from_json
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


def adjust_db_for_map_layer_relation():
    logger.info(f'    Alter DB prime schema map_layer table for UUID')

    statement = f'''
    ALTER TABLE {DB_SCHEMA}.map_layer ADD COLUMN IF NOT EXISTS
    layer_uuid  uuid default null;'''
    db_util.run_statement(statement)
    statement = f'''
    ALTER TABLE {DB_SCHEMA}.map_layer ALTER COLUMN layer_workspace DROP NOT NULL;'''
    db_util.run_statement(statement)
    statement = f'''
    ALTER TABLE {DB_SCHEMA}.map_layer ALTER COLUMN layer_name DROP NOT NULL;'''
    db_util.run_statement(statement)


def adjust_db_for_created_at():
    logger.info(f'    Alter DB prime schema for storing created_at')
    statement = f'ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP;'
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
    order by w.name, p.type, p.name
    ;'''
    publications = db_util.run_query(query, (MAP_TYPE, settings.EnumWfsWmsStatus.AVAILABLE.value, ))

    for workspace, publ_type, publication in publications:
        logger.info(f'    Adjust description of {publ_type} {workspace}.{publication}')
        try:
            if publ_type == LAYER_TYPE:
                wms = get_wms_capabilities(geoserver_workspace=f'{workspace}_wms')
                description = wms.contents[publication].abstract
            else:
                description = ''
                map_json_path = f"{settings.LAYMAN_DATA_DIR}/workspaces/{workspace}/maps/{publication}/input_file/{publication}.json"
                if os.path.exists(map_json_path):
                    with open(map_json_path, 'r', encoding="utf-8") as map_file:
                        map_json = json.load(map_file)
                    description = map_json['abstract'] or ''
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


def adjust_publications_created_at():
    logger.info(f'    Adjust created_at of publications')

    query = f'''select w.name, p.type, p.name, p.uuid
    from {DB_SCHEMA}.publications p inner join
         {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
    where p.type = %s
       or p.wfs_wms_status = %s
    order by w.name, p.type, p.name
    ;'''
    publications = db_util.run_query(query, (MAP_TYPE, settings.EnumWfsWmsStatus.AVAILABLE.value, ))

    update = f'''UPDATE {DB_SCHEMA}.publications SET created_at = %s WHERE uuid = %s'''

    for workspace, publ_type, publication, uuid in publications:
        logger.info(f'    Adjust created_at of {publ_type} {workspace}.{publication}')
        uuid_file_path = os.path.join(util.get_publication_dir(publ_type, workspace, publication),
                                      'uuid.txt')
        created_at = datetime.fromtimestamp(os.path.getmtime(uuid_file_path))
        db_util.run_statement(update, (created_at, uuid))
        os.remove(uuid_file_path)

    logger.info(f'    Adjusting publications created_at DONE')

    alter_tabel = f'''ALTER TABLE {DB_SCHEMA}.publications ALTER COLUMN created_at  SET NOT NULL;'''
    db_util.run_statement(alter_tabel)


def adjust_map_layer_data():
    logger.info(f'    Adjust UUID of layers in map_layer table')

    update = f'''
update {DB_SCHEMA}.map_layer
set layer_uuid = p.uuid
from {DB_SCHEMA}.publications p inner join
     {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
where p.type = %s
  and p.name = layer_name
  and w.name = layer_workspace
    ;'''
    db_util.run_statement(update, (LAYER_TYPE, ))

    # Log rows before delete
    logger.info(f'    Deleting map_layer rows for non-existing layers:')
    query = f'''
    select w.name, p.name, ml.layer_workspace, ml.layer_name
    from {DB_SCHEMA}.map_layer ml inner join
         {DB_SCHEMA}.publications p on ml.id_map = p.id inner join
         {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
    where layer_uuid is null
    order by w.name, p.name, ml.layer_workspace, ml.layer_name
;'''
    rows_to_delete = db_util.run_query(query)
    for map_ws, map_name, layer_ws, layer_name in rows_to_delete:
        logger.info(f'      Delete relation between map {map_ws}.{map_name} and layer {layer_ws}.{layer_name}')

    delete = f'''
    delete from {DB_SCHEMA}.map_layer
    where layer_uuid is null
    ;'''
    db_util.run_statement(delete)

    db_util.run_statement(f'''
    alter table {DB_SCHEMA}.map_layer
      DROP COLUMN layer_name,
      DROP COLUMN layer_workspace,
      ALTER COLUMN layer_uuid SET NOT NULL
      ;''')

    logger.info(f'    Adjust UUID of layers in map_layer table DONE')


def ensure_layers_db_schema():
    logger.info(f'    Ensure DB schema')
    statement = sql.SQL("""CREATE SCHEMA IF NOT EXISTS {schema} AUTHORIZATION {user}""").format(
        schema=sql.Identifier(layer_db.LAYERS_SCHEMA),
        user=sql.Identifier(settings.LAYMAN_PG_USER),
    )
    db_util.run_statement(statement)


def ensure_gs_workspaces_and_stores():
    logger.info(f'    Ensure GS workspaces and data stores')
    all_gs_workspaces = gs_util.get_all_workspaces(auth=settings.LAYMAN_GS_AUTH)
    assert names.GEOSERVER_WFS_WORKSPACE not in all_gs_workspaces
    assert names.GEOSERVER_WMS_WORKSPACE not in all_gs_workspaces
    gs_util.ensure_workspace(names.GEOSERVER_WFS_WORKSPACE, auth=settings.LAYMAN_GS_AUTH)
    gs_util.ensure_workspace(names.GEOSERVER_WMS_WORKSPACE, auth=settings.LAYMAN_GS_AUTH)

    gs_util.ensure_db_store(names.GEOSERVER_WFS_WORKSPACE, db_schema=layer_db.LAYERS_SCHEMA, pg_conn=settings.PG_CONN,
                            name=DEFAULT_INTERNAL_DB_STORE, auth=settings.LAYMAN_GS_AUTH)
    gs_util.ensure_db_store(names.GEOSERVER_WMS_WORKSPACE, db_schema=layer_db.LAYERS_SCHEMA, pg_conn=settings.PG_CONN,
                            name=DEFAULT_INTERNAL_DB_STORE, auth=settings.LAYMAN_GS_AUTH)


def delete_layers_without_wfs_wms_available():
    logger.info(f'    Delete layers that do not have WFS/WMS available')

    query = f'''select w.name, p.name, p.uuid::varchar as uuid, p.id
    from {DB_SCHEMA}.publications p inner join
         {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
    where p.type = %s and p.wfs_wms_status != %s
    order by w.name, p.name
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
        query = f'''delete from {DB_SCHEMA}.rights where id_publication = %s;'''
        db_util.run_statement(query, (layer_id,))
        query = f"""delete from {DB_SCHEMA}.publications p where p.id = %s;"""
        db_util.run_statement(query, (layer_id,))

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
    select w.name, p.name, p.uuid::varchar as uuid, p.style_type, p.title, p.description, p.image_mosaic, p.geodata_type,
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
    order by w.name, p.name
    ;'''
    layers = db_util.run_query(query, (LAYER_TYPE,))
    failed_layers = {}
    layer_number = 0
    layer_cnt = len(layers)

    for workspace, layername, layer_uuid, style_type_code, title, description, image_mosaic, geodata_type, external_table_uri, \
            read_users_roles, write_users_roles in layers:
        failed_steps = []
        layer_number += 1

        # check if publication is not yet migrated
        publ_info = get_complete_layer_info(workspace, layername)
        publ_status = publ_info['layman_metadata']['publication_status']
        assert publ_status in ['COMPLETE', 'INCOMPLETE']
        if publ_status == 'INCOMPLETE':
            logger.info(f'    Migrate layer {workspace}.{layername} (uuid={layer_uuid}), {layer_number}/{layer_cnt}')
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
            layer_dir = f"{settings.LAYMAN_NORMALIZED_RASTER_DATA_DIR}/workspaces/{workspace}/layers/{layername}"
            time_regex_props = get_timeregex_props(layer_dir)
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

        src_main_path = f"{settings.LAYMAN_DATA_DIR}/workspaces/{workspace}/layers/{layername}"
        dst_main_path = f"{settings.LAYMAN_DATA_DIR}/layers/{layer_uuid}"

        shutil.rmtree(f"{src_main_path}/input_chunk", ignore_errors=True)

        # Move input files
        if original_data_source == settings.EnumOriginalDataSource.FILE.value:
            logger.info("      moving input files")
            new_path = layer_file_util.get_layer_dir(layer_uuid)
            input_file.ensure_layer_input_file_dir(layer_uuid)
            input_files = util.get_layer_input_files(workspace, layername)
            name_input_file_by_layer = not image_mosaic or input_files.is_one_archive
            try:
                for filename in input_files.raw_paths:
                    base_filename = os.path.basename(filename)
                    dst_filename = f'{layer_uuid}{base_filename[len(layername):]}' if name_input_file_by_layer else base_filename
                    dst_path = os.path.join(new_path, 'input_file', dst_filename)
                    shutil.move(filename, dst_path)
                os.rmdir(f"{src_main_path}/input_file")
            except BaseException:
                failed_steps.append('input_file')
                logger.error(f'    Fail to move input files: : \n{traceback.format_exc()}')

        # Move style files
        old_style_dir = f"{src_main_path}/input_style"
        try:
            if os.path.isdir(old_style_dir):
                logger.info("      moving style file")
                dst_style_path = f"{dst_main_path}/input_style/{layer_uuid}.{style_type.extension}"
                src_style_path = f"{old_style_dir}/{layername}.{style_type.extension}"
                os.makedirs(f"{dst_main_path}/input_style/", exist_ok=True)
                shutil.move(src_style_path, dst_style_path)
                os.rmdir(f"{old_style_dir}")
        except BaseException:
            failed_steps.append('input_style')
            logger.error(f'    Fail to move style file: : \n{traceback.format_exc()}')

        # move normalized raster files
        gdal_old_dir = f"{settings.LAYMAN_NORMALIZED_RASTER_DATA_DIR}/workspaces/{workspace}/layers/{layername}"
        if geodata_type == settings.GEODATA_TYPE_RASTER:
            logger.info("      moving normalized raster files")
            try:
                gdal.ensure_normalized_raster_layer_dir(layer_uuid)
                gdal_dir = gdal.get_normalized_raster_layer_dir(layer_uuid)
                if image_mosaic:
                    for filename in [
                        'sample_image.dat',
                        f'{layername}.dbf',
                        f'{layername}.fix',
                        f'{layername}.prj',
                        f'{layername}.properties',
                        f'{layername}.qix',
                        f'{layername}.shp',
                        f'{layername}.shx',
                    ]:
                        filepath = os.path.join(gdal_old_dir, filename)
                        os.remove(filepath)

                    for filename in [
                        'indexer.properties',
                        'timeregex.properties',
                    ]:
                        src_filepath = os.path.join(gdal_old_dir, filename)
                        dst_filepath = os.path.join(gdal_dir, filename)
                        shutil.move(src_filepath, dst_filepath)

                all_filenames = set(
                    os.path.basename(filename) for filename in os.listdir(gdal_old_dir))
                tif_filenames = set(
                    os.path.splitext(filename)[0] for filename in all_filenames if filename.endswith('.tif'))
                main_filenames = set(tif_filename for tif_filename in tif_filenames if tif_filename == layername or image_mosaic)
                for src_filename in main_filenames:
                    file_to_move = {filename for filename in all_filenames if filename.startswith(f'{src_filename}.tif')}
                    for filename in file_to_move:
                        dst_filename = f'{layer_uuid}{filename[len(layername):]}' if not image_mosaic else filename
                        src_filepath = os.path.join(gdal_old_dir, filename)
                        dst_filepath = os.path.join(gdal_dir, dst_filename)
                        shutil.move(src_filepath, dst_filepath)
                os.rmdir(gdal_old_dir)
            except BaseException:
                failed_steps.append('normalized_raster_files')
                logger.error(f'    Fail to move normalized raster files: : \n{traceback.format_exc()}')

        # move layer in DB
        if geodata_type == settings.GEODATA_TYPE_VECTOR \
                and original_data_source == settings.EnumOriginalDataSource.FILE.value:
            if not layer_db_table.get_layer_info(workspace, layername):
                logger.info("      moving table in DB")
                layer_table = f"layer_{layer_uuid.replace('-', '_')}"
                try:
                    # move table
                    statement = sql.SQL('''
                    ALTER TABLE {layer_table} SET SCHEMA layers;
                    ''').format(
                        layer_table=sql.Identifier(workspace, layer_table)
                    )
                    db_util.run_statement(statement)

                    # rename indexes
                    new_pkey_index = f"{layer_table}_pkey"
                    statement = sql.SQL('''
                    ALTER INDEX IF EXISTS {old_pkey_index} RENAME TO {new_pkey_index};
                    ''').format(
                        old_pkey_index=sql.Identifier('layers', f"{layername}_pkey"),
                        new_pkey_index=sql.Identifier(new_pkey_index),
                    )
                    db_util.run_statement(statement)

                    new_geom_index = f"{layer_table}_wkb_geometry_geom_id"
                    statement = sql.SQL('''
                    ALTER INDEX IF EXISTS {old_geom_index} RENAME TO {new_geom_index};
                    ''').format(
                        old_geom_index=sql.Identifier('layers', f"{layername}_wkb_geometry_geom_idx"),
                        new_geom_index=sql.Identifier(new_geom_index),
                    )
                    db_util.run_statement(statement)

                    # rename sequences
                    new_pkey_seq = f"{layer_table}_ogc_fid_seq"
                    for old_pkey_seq in [f"{layername}_ogc_fid_seq", f"{layername}_id_seq"]:
                        statement = sql.SQL('''
                        ALTER SEQUENCE IF EXISTS {old_pkey_seq} RENAME TO {new_pkey_seq};
                        ''').format(
                            old_pkey_seq=sql.Identifier('layers', old_pkey_seq),
                            new_pkey_seq=sql.Identifier(new_pkey_seq),
                        )
                        db_util.run_statement(statement)

                    # check indexes
                    query = sql.SQL('''
                    select indexname from pg_indexes
                    where schemaname = 'layers' and tablename = {layer_table};
                    ''').format(
                        layer_table=sql.Literal(layer_table)
                    )
                    rows = db_util.run_query(query)
                    exp_indexes = {new_pkey_index, new_geom_index}
                    found_indexes = {row[0] for row in rows}
                    assert found_indexes == exp_indexes, f"found_indexes={found_indexes}, exp_indexes={exp_indexes}"

                    # check sequences
                    query = sql.SQL('''
                    select seq_ns.nspname as sequence_schema,
                           seq.relname as sequence_name,
                           tab_ns.nspname as table_schema,
                           tab.relname as related_table
                    from pg_class seq
                        join pg_namespace seq_ns on seq.relnamespace = seq_ns.oid
                        JOIN pg_depend d ON d.objid = seq.oid
                        JOIN pg_class tab ON d.refobjid = tab.oid
                        JOIN pg_namespace tab_ns on tab.relnamespace = tab_ns.oid
                    where seq.relkind = 'S'
                    and tab_ns.nspname = 'layers' and tab.relname={layer_table}
                    ''').format(
                        layer_table=sql.Literal(layer_table)
                    )
                    rows = db_util.run_query(query)
                    found_sequences = {(row[0], row[1]) for row in rows}
                    exp_sequences = {('layers', new_pkey_seq)}
                    assert found_sequences == exp_sequences, f"exp_sequences={exp_sequences}, all_sequences={found_sequences}"

                except BaseException:
                    failed_steps.append('db_table')
                    logger.error(f'    Fail to move DB table to global schema: : \n{traceback.format_exc()}')
            else:
                logger.warning("      table in DB already exists in global schema!")

        # re-create QGIS files
        old_qgis_path = f"{settings.LAYMAN_QGIS_DATA_DIR}/workspaces/{workspace}/layers/{layername}"
        if style_type.code == 'qml':
            logger.info("      re-creating QGIS files")
            try:
                shutil.rmtree(old_qgis_path, ignore_errors=True)
                util.run_task_sync(qgis_refresh_wms, [workspace, layername], post_task_kwargs)
            except BaseException:
                failed_steps.append('qgis')
                logger.error(f'    Fail to move qgis file: : \n{traceback.format_exc()}')

        # delete layer from geoserver
        util.delete_layer_from_geoserver_v1_23(layername, workspace)

        # re-create layer on geoserver
        if not wfs.get_layer_info_by_uuid(uuid=layer_uuid):
            logger.info("      re-creating geoserver.wfs")
            try:
                util.run_task_sync(refresh_wfs, [workspace, layername], post_task_kwargs)
            except BaseException:
                failed_steps.append('geoserver_wfs')
                logger.error(f'    Fail to recreate layer in GeoServer WFS workspace: : \n{traceback.format_exc()}')
        else:
            logger.warning("      geoserver.wfs already exists!")

        if not gs_wms.get_layer_info_by_uuid(uuid=layer_uuid):
            logger.info("      re-creating geoserver.wms")
            try:
                util.run_task_sync(refresh_wms, [workspace, layername], post_task_kwargs)
            except BaseException:
                failed_steps.append('geoserver_wms')
                logger.error(f'    Fail to recreate layer in GeoServer WMS workspace: : \n{traceback.format_exc()}')
        else:
            logger.warning("      geoserver.wms already exists!")

        if not sld.get_layer_info_by_uuid(workspace, uuid=layer_uuid, layername=layername):
            logger.info("      re-creating geoserver.sld")
            try:
                util.run_task_sync(refresh_sld, [workspace, layername], post_task_kwargs)
            except BaseException:
                failed_steps.append('geoserver_sld')
                logger.error(f'    Fail to recreate style in GeoServer: \n{traceback.format_exc()}')
        else:
            logger.warning("      geoserver.sld already exists!")

        # Move thumbnail file
        logger.info("      moving thumbnail file")
        src_thumbnail_path = f"{src_main_path}/thumbnail/{layername}.png"
        dst_thumbnail_path = f"{dst_main_path}/thumbnail/{layer_uuid}.png"
        check_thumbnail_key = False
        try:
            if os.path.exists(src_thumbnail_path):
                check_thumbnail_key = True
                os.makedirs(f"{dst_main_path}/thumbnail/", exist_ok=True)
                shutil.move(src_thumbnail_path, dst_thumbnail_path)
                os.rmdir(f"{src_main_path}/thumbnail")
            else:
                util.safe_delete(f"{src_main_path}/thumbnail")
        except BaseException:
            failed_steps.append('thumbnail')
            logger.error(f'    Fail to move thumbnail file: : \n{traceback.format_exc()}')

        # assert that source keys up to geoserver are OK
        if not failed_steps:
            publ_info = get_complete_layer_info(workspace, layername)
            keys_to_check = ['wms', 'style']
            if publ_info['geodata_type'] == 'vector':
                keys_to_check += ['db', 'wfs']
            if publ_info['original_data_source'] == 'file':
                keys_to_check += ['file']
            if check_thumbnail_key:
                keys_to_check += ['thumbnail']
            assert all('status' not in publ_info[key] for key in keys_to_check), json.dumps(publ_info, indent=2)
            os.rmdir(f"{src_main_path}")
        else:
            util.safe_delete(src_main_path)
            failed_layers[(workspace, layername, layer_uuid)] = failed_steps

        logger.info(f'    Migrate layer {workspace}.{layername} DONE')

    if failed_layers:
        warning = f'  These layers were not migrated successfully:\n'
        for layer_ws_name_uuid, failed_steps in failed_layers.items():
            workspace, layername, layer_uuid = layer_ws_name_uuid
            warning += f'    {workspace}.{layername} (uuid={layer_uuid}): {failed_steps}\n'
        logger.warning(warning)


def migrate_map_file_layer_names(layers_str: str, layer_name, layer_uuid, layer_ws) -> str:
    layers = layers_str.split(',')
    for layer_idx, full_layername in enumerate(layers):
        layer_parts = full_layername.split(':')
        if len(layer_parts) == 1:
            if layer_parts[0] == layer_name:
                layers[layer_idx] = f'l_{layer_uuid}'
        elif len(layer_parts) == 2:
            if layer_parts[0] in [f'{layer_ws}_wms', f'{layer_ws}'] and layer_parts[1] == layer_name:
                wspace = 'layman_wms' if layer_parts[0] == f'{layer_ws}_wms' else 'layman'
                layers[layer_idx] = f'{wspace}:l_{layer_uuid}'
    return ','.join(layers)


def migrate_map_file(map_file_path, map_layers):
    with open(map_file_path, 'r', encoding="utf-8") as map_file:
        map_json = json.load(map_file)
    for map_layer in map_layers:
        layer_index = map_layer['index']
        layer_uuid = map_layer['uuid']
        layer_ws = map_layer['workspace']
        layer_name = map_layer['name']

        layer_def = map_json['layers'][layer_index]
        class_name = layer_def.get('className', '').split('.')[-1]
        if class_name == 'WMS':
            layer_def['url'] = layer_def['url'].replace(f'/geoserver/{layer_ws}_wms/', f'/geoserver/layman_wms/').replace(f'/geoserver/{layer_ws}/', f'/geoserver/layman/')
            old_layers = layer_def['params']['LAYERS']
            new_layers = migrate_map_file_layer_names(old_layers, layer_name, layer_uuid, layer_ws)
            layer_def['params']['LAYERS'] = new_layers
        elif class_name == 'Vector':
            layer_def['protocol']['url'] = layer_def['protocol']['url'].replace(f'/{layer_ws}/', f'/layman/').replace(
                f'/{layer_ws}_wms/', f'/layman_wms/')
            old_layers = layer_def['name']
            new_layers = migrate_map_file_layer_names(old_layers, layer_name, layer_uuid, layer_ws)
            layer_def['name'] = new_layers
        else:
            raise ValueError(f'Unknown layer type: {layer_def["type"]}')

    new_layers = get_layers_from_json(map_json)
    old_layers = [(layer['uuid'], layer['index']) for layer in map_layers]
    new_layers.sort(key=lambda x: (x[1], x[0]))
    old_layers.sort(key=lambda x: (x[1], x[0]))
    if new_layers != old_layers:
        new_map_file_path = map_file_path + '.new'
        with open(new_map_file_path, 'w', encoding="utf-8") as map_file:
            json.dump(map_json, map_file, indent=4)
        assert new_layers == old_layers, f'New internal layers do not correspond to the old ones. New file saved as {new_map_file_path}.\n{new_layers=}\n{old_layers=}'

    with open(map_file_path, 'w', encoding="utf-8") as map_file:
        json.dump(map_json, map_file, indent=4)


def migrate_maps():
    logger.info(f'    Migrate maps')

    query = f'''
    select w.name,
           p.name,
           p.uuid::varchar as uuid,
           (select json_agg(json_build_object(
                   'name', lr.name,
                   'workspace', layer_ws.name,
                   'index', ml.layer_index,
                   'uuid', ml.layer_uuid
                   ) order by ml.layer_index, layer_ws.name, lr.name)
        from {DB_SCHEMA}.map_layer ml left join
             {DB_SCHEMA}.publications lr inner join
             {DB_SCHEMA}.workspaces layer_ws on lr.id_workspace = layer_ws.id
                                         on ml.layer_uuid = lr.uuid
        where ml.id_map = p.id) map_layers
    from {DB_SCHEMA}.publications p inner join
         {DB_SCHEMA}.workspaces w on w.id = p.id_workspace left join
         {DB_SCHEMA}.users u on u.id_workspace = w.id
    where p.type = %s
    order by w.name, p.name
    ;'''
    maps = db_util.run_query(query, (MAP_TYPE,))
    failed_maps = {}
    map_number = 0
    map_cnt = len(maps)

    for workspace, mapname, map_uuid, map_layers, in maps:
        failed_steps = []
        map_number += 1

        # check if publication is not yet migrated
        publ_info = get_complete_map_info(workspace, mapname)
        publ_status = publ_info['layman_metadata']['publication_status']
        assert publ_status in ['COMPLETE', 'INCOMPLETE']
        if publ_status == 'INCOMPLETE':
            logger.info(f'    Migrate map {workspace}.{mapname} (uuid={map_uuid}), {map_number}/{map_cnt}')
        else:
            logger.warning(f'    Map {workspace}.{mapname} seems already migrated!')
            continue

        src_main_path = f"{settings.LAYMAN_DATA_DIR}/workspaces/{workspace}/maps/{mapname}"
        dst_main_path = f"{settings.LAYMAN_DATA_DIR}/maps/{map_uuid}"

        # Move input files
        logger.info("      moving input files")
        try:
            src_input_file_path = f"{src_main_path}/input_file/{mapname}.json"
            dst_input_filepath = f"{dst_main_path}/input_file/{map_uuid}.json"
            os.makedirs(f"{dst_main_path}/input_file/", exist_ok=True)
            shutil.move(src_input_file_path, dst_input_filepath)
            os.rmdir(f"{src_main_path}/input_file")
        except BaseException:
            failed_steps.append('input_file')
            logger.error(f'    Fail to move input files: : \n{traceback.format_exc()}')

        # Migrate layers in map file
        map_file_path = f"{dst_main_path}/input_file/{map_uuid}.json"
        if map_layers:
            migrate_map_file(map_file_path, map_layers)
        else:
            with open(map_file_path, 'r', encoding="utf-8") as map_file:
                map_json = json.load(map_file)
            new_layers = get_layers_from_json(map_json)
            assert new_layers == [], f'Still no internal layer should be found.'

        # Move thumbnail file
        logger.info("      moving thumbnail file")
        src_thumbnail_path = f"{src_main_path}/thumbnail/{mapname}.png"
        dst_thumbnail_path = f"{dst_main_path}/thumbnail/{map_uuid}.png"
        check_thumbnail_key = False
        if os.path.exists(src_thumbnail_path):
            check_thumbnail_key = True
            try:
                os.makedirs(f"{dst_main_path}/thumbnail/", exist_ok=True)
                shutil.move(src_thumbnail_path, dst_thumbnail_path)
                os.rmdir(f"{src_main_path}/thumbnail")
            except BaseException:
                failed_steps.append('thumbnail')
                logger.error(f'    Fail to move thumbnail file: : \n{traceback.format_exc()}')
        else:
            util.safe_delete(f"{src_main_path}/thumbnail")

        # assert that source keys up to geoserver are OK
        if not failed_steps:
            publ_info = get_complete_map_info(workspace, mapname)
            keys_to_check = ['file']
            if check_thumbnail_key:
                keys_to_check += ['thumbnail']
            assert all('status' not in publ_info[key] for key in keys_to_check), json.dumps(publ_info, indent=2)
        else:
            failed_maps[(workspace, mapname, map_uuid)] = failed_steps

        os.rmdir(f"{src_main_path}")
        logger.info(f'    Migrate map {workspace}.{mapname} DONE')

    if failed_maps:
        warning = f'  These maps were not migrated successfully:\n'
        for map_ws_name_uuid, failed_steps in failed_maps.items():
            workspace, mapname, map_uuid = map_ws_name_uuid
            warning += f'    {workspace}.{mapname} (uuid={map_uuid}): {failed_steps}\n'
        logger.warning(warning)


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

        # db
        statement = f'''
        DROP SCHEMA IF EXISTS {workspace};
        '''
        db_util.run_statement(statement)

        util.safe_delete(f"{settings.LAYMAN_DATA_DIR}/workspaces/{workspace}/layers")
        util.safe_delete(f"{settings.LAYMAN_DATA_DIR}/workspaces/{workspace}/maps")
        util.safe_delete(f"{settings.LAYMAN_DATA_DIR}/workspaces/{workspace}")

        util.safe_delete(f"{settings.LAYMAN_QGIS_DATA_DIR}/workspaces/{workspace}/layers")
        util.safe_delete(f"{settings.LAYMAN_QGIS_DATA_DIR}/workspaces/{workspace}")
        util.safe_delete(f"{settings.LAYMAN_NORMALIZED_RASTER_DATA_DIR}/workspaces/{workspace}/layers")
        util.safe_delete(f"{settings.LAYMAN_NORMALIZED_RASTER_DATA_DIR}/workspaces/{workspace}")

    util.safe_delete(f"{settings.LAYMAN_QGIS_DATA_DIR}/workspaces", warn_OSError=True)

    util.safe_delete(f"{settings.LAYMAN_NORMALIZED_RASTER_DATA_DIR}/workspaces", warn_OSError=True)

    util.safe_delete(f"{settings.LAYMAN_DATA_DIR}/workspaces", warn_OSError=True)
    logger.info(f'    Delete old workspaces DONE!')
