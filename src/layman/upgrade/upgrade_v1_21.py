import json
import logging
from urllib.parse import urljoin
import requests

from db import util as db_util
from geoserver import GS_REST_WORKSPACES, GS_REST_TIMEOUT, util as gs_common_util
from layman import settings
from layman.common.micka import util as micka_util
from layman.layer import LAYER_TYPE, util
from layman.layer.geoserver import wms, util as gs_util
from layman.map import MAP_TYPE

logger = logging.getLogger(__name__)
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def adjust_db_for_wfs_wms_status():
    logger.info(f'    Alter DB prime schema for wfs_wms_status')
    status_string = ", ".join([f"'{status.value}'" for status in settings.EnumWfsWmsStatus])

    statement = f'''
    DO $$ BEGIN
        CREATE TYPE {DB_SCHEMA}.enum_wfs_wms_status AS ENUM ({status_string});
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
        ALTER TABLE {DB_SCHEMA}.publications ADD COLUMN IF NOT EXISTS
        wfs_wms_status {DB_SCHEMA}.enum_wfs_wms_status;'''

    db_util.run_statement(statement)


def adjust_publications_wfs_wms_status():
    logger.info(f'    Adjust wfs_wms_status of publications')

    query = f'''select w.name,
        p.name
    from {DB_SCHEMA}.publications p inner join
         {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
    where p.type = %s
    ;'''
    publications = db_util.run_query(query, (LAYER_TYPE, ))

    for workspace, publication_name in publications:
        util.set_wfs_wms_status_after_fail(workspace, publication_name, )

    statement = f'alter table {DB_SCHEMA}.publications add constraint wfs_wms_status_with_type_check CHECK ' \
                f'((wfs_wms_status IS NULL AND type = %s) OR (wfs_wms_status IS NOT NULL AND type = %s));'
    db_util.run_statement(statement, (MAP_TYPE, LAYER_TYPE,))


def adjust_layer_metadata_url_on_gs():
    logger.info(f'    Adjust layer MetadataUrl on GeoServer')

    auth = settings.LAYMAN_GS_AUTH

    query = f'''select w.name, p.name, p.geodata_type, p.style_type, p.image_mosaic, p.uuid, PGP_SYM_DECRYPT(p.external_table_uri, p.uuid::text)::json external_table_uri
    from {DB_SCHEMA}.publications p inner join
         {DB_SCHEMA}.workspaces w on w.id = p.id_workspace
    where p.type = %s
      and p.wfs_wms_status = %s
    ;'''
    layers = db_util.run_query(query, (LAYER_TYPE, settings.EnumWfsWmsStatus.AVAILABLE.value))

    for workspace, layer, geodata_type, style_type, image_mosaic, uuid, external_table_uri in layers:
        logger.info(f'      Layer {workspace}:{layer}')
        wms_workspace = wms.get_geoserver_workspace(workspace)

        metadata_links = {
            'metadataLinks':
                {
                    "metadataLink": [
                        {
                            "type": "application/xml",
                            "metadataType": "ISO19115:2003",
                            "content": micka_util.get_metadata_url(uuid, url_type=micka_util.RecordUrlType.XML),
                        }
                    ]
                }
        }

        if geodata_type == settings.GEODATA_TYPE_RASTER:
            wms_body = {"coverage": metadata_links}
            store_name = wms.get_image_mosaic_store_name(layer) if image_mosaic else wms.get_geotiff_store_name(layer)
            wms_url = urljoin(GS_REST_WORKSPACES, f'{wms_workspace}/coveragestores/{store_name}/coverages/{layer}')
        elif geodata_type == settings.GEODATA_TYPE_VECTOR:
            if style_type == 'sld':
                wms_body = {"featureType": metadata_links}
                store_name = gs_util.get_external_db_store_name(layer) if external_table_uri else gs_common_util.DEFAULT_DB_STORE_NAME
                wms_url = urljoin(GS_REST_WORKSPACES, f'{wms_workspace}/datastores/{store_name}/featuretypes/{layer}')
            elif style_type == 'qml':
                wms_layer = gs_common_util.get_wms_layer(wms_workspace, layer, auth=auth)
                wms_layer = {**wms_layer, **metadata_links}
                wms_body = {"wmsLayer": wms_layer}
                wms_url = urljoin(GS_REST_WORKSPACES, f'{wms_workspace}/wmslayers/{layer}')
            else:
                raise NotImplementedError(f"Unknown style type: {style_type}")

            # WFS
            wfs_body = {"featureType": metadata_links}
            wfs_store = gs_util.get_external_db_store_name(layer) if external_table_uri else gs_common_util.DEFAULT_DB_STORE_NAME
            response = requests.put(
                urljoin(GS_REST_WORKSPACES, f'{workspace}/datastores/{wfs_store}/featuretypes/{layer}'),
                data=json.dumps(wfs_body),
                headers=gs_common_util.headers_json,
                auth=auth,
                timeout=GS_REST_TIMEOUT,
            )
            response.raise_for_status()
        elif geodata_type == settings.GEODATA_TYPE_UNKNOWN:
            continue
        else:
            raise NotImplementedError(f"Unknown geodata type: {geodata_type}")

        # WMS
        response = requests.put(
            wms_url,
            data=json.dumps(wms_body),
            headers=gs_common_util.headers_json,
            auth=auth,
            timeout=GS_REST_TIMEOUT,
        )
        response.raise_for_status()
