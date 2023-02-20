import json
import logging
from urllib.parse import urljoin
import requests

from db import util as db_util
import geoserver
from geoserver import util as gs_util
from layman import settings, util as layman_util
from layman.layer import LAYER_TYPE
from layman.layer.geoserver import wms as gs_wms, wfs as gs_wfs
from layman.layer.qgis import wms as qgis_wms
from layman.map import MAP_TYPE

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def adjust_db_for_file_type():
    logger.info(f'    Alter DB prime schema for file type')

    statement = f'''
    DO $$ BEGIN
        CREATE TYPE {DB_SCHEMA}.enum_file_type AS ENUM ('vector', 'raster', 'unknown');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
        ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS
        file_type {DB_SCHEMA}.enum_file_type;'''

    db_util.run_statement(statement)


def adjust_publications_file_type():
    logger.info(f'    Adjust file type of publications')
    query = f'''select w.name, p.type, p.name
    from {DB_SCHEMA}.publications p inner join
         {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
    where p.type = %s
    ;'''
    publications = db_util.run_query(query, (LAYER_TYPE, ))

    for workspace, publ_type, publication in publications:
        file_type = None
        logger.info(f'    Adjust file type of {publ_type} {workspace}.{publication}')
        file_type = layman_util.get_publication_info(workspace, publ_type, publication,
                                                     context={'keys': ['file']})['file']['file_type']

        query = f'''update {DB_SCHEMA}.publications set
        geodata_type = %s
        where type = %s
          and name = %s
          and id_workspace = (select w.id from {DB_SCHEMA}.workspaces w where w.name = %s);'''
        params = (file_type, publ_type, publication, workspace,)
        db_util.run_statement(query, params)

    logger.info(f'    Adjusting publications file type DONE')


def adjust_db_publication_file_type_constraint():
    statement = f'alter table {DB_SCHEMA}.publications add constraint file_type_with_publ_type_check CHECK ' \
                f'((type = %s AND geodata_type IS NULL) OR (type = %s AND geodata_type IS NOT NULL));'
    db_util.run_statement(statement, (MAP_TYPE, LAYER_TYPE))


def rename_table_names():
    logger.info(f'    Rename vector data DB table name to `layer_<uuid>`')
    query = f'''select w.name, p.type, p.name
    from {DB_SCHEMA}.publications p inner join
         {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
    where p.type = %s
    ;'''
    publications = db_util.run_query(query, (LAYER_TYPE, ))

    for workspace, publ_type, publication in publications:
        logger.info(f'    Table name for {publ_type} {workspace}.{publication}')
        publ_info = layman_util.get_publication_info(workspace, publ_type, publication,
                                                     context={'keys': ['file', 'uuid', 'style_type', ]})
        file_type = publ_info['file']['file_type']
        uuid = publ_info['uuid']
        style_type = publ_info['_style_type']
        table_name = f'layer_{uuid.replace("-", "_")}'

        if file_type == settings.GEODATA_TYPE_VECTOR:
            query = f"""
            SELECT count(*)
            FROM information_schema.tables
            WHERE table_schema = %s
            AND table_name = %s
            """
            result = db_util.run_query(query, (workspace, publication))

            if result[0][0] == 0:
                logger.info(f'      Table {workspace}.{publication} does not exists in DB')
                continue

            query = f'''
            ALTER TABLE {workspace}.{publication} RENAME TO {table_name};
            '''
            db_util.run_statement(query,)

            # WFS workspace GS
            wfs_info = gs_wfs.get_layer_info(workspace, publication)

            if 'wfs' not in wfs_info:
                logger.info(f'      Layer {workspace}.{publication} does not exists on GeoServer')
                continue

            # WFS workspace GS
            ftype = {'nativeName': table_name}
            body = {
                "featureType": ftype
            }
            response = requests.put(
                urljoin(geoserver.GS_REST_WORKSPACES,
                        workspace + '/datastores/postgresql/featuretypes/' + publication),
                data=json.dumps(body),
                headers=gs_util.headers_json,
                auth=geoserver.GS_AUTH,
                timeout=geoserver.GS_REST_TIMEOUT,
            )
            response.raise_for_status()

            # WMS workspace
            if style_type == 'sld':
                wms_workspace = gs_wms.get_geoserver_workspace(workspace)

                wfs_info = gs_wfs.get_layer_info(wms_workspace, publication)

                if 'wfs' not in wfs_info:
                    logger.info(f'      Layer {wms_workspace}.{publication} does not exists on GeoServer')
                    continue

                response = requests.put(
                    urljoin(geoserver.GS_REST_WORKSPACES,
                            wms_workspace + '/datastores/postgresql/featuretypes/' + publication),
                    data=json.dumps(body),
                    headers=gs_util.headers_json,
                    auth=geoserver.GS_AUTH,
                    timeout=geoserver.GS_REST_TIMEOUT,
                )
                response.raise_for_status()
            elif style_type == 'qml':
                qgis_wms.save_qgs_file(workspace, publication)
            else:
                raise NotImplementedError(f"Unknown style type: {style_type} of layer {workspace}.{publication}")
