import io
import json
import logging
import re
import requests
import time
import os
from urllib.parse import urljoin
from layman import settings
from layman.http import LaymanError
from layman.common import prime_db_schema
from layman.common import geoserver as gs_common
from layman.common.prime_db_schema import workspaces, util as db_util
from layman import util
from layman.layer import LAYER_TYPE
from layman.layer import geoserver
from layman.layer.geoserver import wms, util as gs_util
from layman.layer.micka import csw as layer_csw
from layman.layer.filesystem import util as layer_fs_util, input_style
from layman.map import MAP_TYPE
from layman.map.filesystem import input_file
from layman.map.micka import csw as map_csw

logger = logging.getLogger(__name__)


def alter_schema():
    logger.info(f'    Starting - alter DB prime schema')
    db_schema = settings.LAYMAN_PRIME_SCHEMA
    add_column = f'''
DO $$ BEGIN
    CREATE TYPE {db_schema}.enum_style_type AS ENUM ('sld', 'qml');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;
    ALTER TABLE {db_schema}.publications ADD COLUMN IF NOT EXISTS
    style_type {db_schema}.enum_style_type;'''
    db_util.run_statement(add_column)
    logger.info(f'    DONE - alter DB prime schema')


def check_workspace_names():
    logger.info(f'    Starting - checking workspace names - for {settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX} suffix, '
                f'for `{settings.REST_WORKSPACES_PREFIX}` name')
    workspaces = prime_db_schema.get_workspaces()
    for workspace in workspaces:
        if workspace.endswith(settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX):
            raise LaymanError(f"A workspace has name with reserved suffix '{settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX}'. "
                              f"In that case, please downgrade to the previous minor release version of Layman and contact Layman "
                              f"contributors. One way how to do that is to create an issue in Layman repository: "
                              f"https://github.com/jirik/layman/issues/",
                              data={'workspace': workspace,
                                    }
                              )
    if settings.REST_WORKSPACES_PREFIX in workspaces:
        raise LaymanError(f"A workspace has reserved name '{settings.REST_WORKSPACES_PREFIX}'. "
                          f"In that case, please downgrade to the previous minor release version of Layman and contact Layman "
                          f"contributors. One way how to do that is to create an issue in Layman repository: "
                          f"https://github.com/jirik/layman/issues/",
                          data={'workspace': settings.REST_WORKSPACES_PREFIX
                                }
                          )
    logger.info(f'    DONE - checking workspace names - for {settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX} suffix, '
                f'for `{settings.REST_WORKSPACES_PREFIX}` name')


def migrate_layers_to_wms_workspace(workspace=None):
    logger.info(f'    Starting - migrate layers to WMS workspace')
    infos = util.get_publication_infos(publ_type=LAYER_TYPE, workspace=workspace)
    for (workspace, publication_type, layer) in infos.keys():
        logger.info(f'      Migrate layer {workspace}.{layer}')
        info = util.get_publication_info(workspace, publication_type, layer)
        geoserver_workspace = wms.get_geoserver_workspace(workspace)
        geoserver.ensure_workspace(workspace)
        if not (info.get('db_table') and info.get('db_table').get('name') == layer):
            logger.warning(f'        Layer DB table not available, not migrating.')
            continue

        r = requests.get(
            urljoin(settings.LAYMAN_GS_REST_WORKSPACES,
                    geoserver_workspace + '/layers/' + layer),
            auth=settings.LAYMAN_GS_AUTH,
            timeout=5,
        )
        if r.status_code == 404:
            geoserver.publish_layer_from_db(workspace,
                                            layer,
                                            info.get('description'),
                                            info.get('title'),
                                            info.get('access_rights'),
                                            geoserver_workspace=geoserver_workspace)
            wms.clear_cache(workspace)
        else:
            r.raise_for_status()
            logger.info(f'        Layer already migrated.')

        sld_wms_r = gs_common.get_workspace_style_response(geoserver_workspace, layer, auth=settings.LAYMAN_GS_AUTH)
        if sld_wms_r.status_code == 404:
            sld_r = gs_common.get_workspace_style_response(workspace, layer, auth=settings.LAYMAN_GS_AUTH)
            if sld_r.status_code == 200:
                sld_stream = io.BytesIO(sld_r.content)
                gs_common.post_workspace_sld_style(geoserver_workspace, layer, sld_stream)
                gs_common.delete_workspace_style(workspace, layer, auth=settings.LAYMAN_GS_AUTH)
                wms.clear_cache(workspace)
            else:
                logger.warning(f"      Error when loading SLD style from GeoServer, status code={sld_r.status_code}, response=\n{sld_r.content}")
        else:
            sld_wms_r.raise_for_status()
            logger.info(f'        Layer SLD style already migrated.')

    logger.info(f'    DONE - migrate layers to WMS workspace')


def migrate_maps_on_wms_workspace():
    logger.info(f'    Starting - migrate maps json urls')
    infos = util.get_publication_infos(publ_type=MAP_TYPE)
    gs_url = gs_util.get_gs_proxy_base_url()
    gs_url = gs_url if gs_url.endswith('/') else f"{gs_url}/"
    gs_wms_url_pattern = r'^' + re.escape(gs_url) + r'(' + util.USERNAME_ONLY_PATTERN + r')' + r'(/(?:ows|wms|wfs).*)$'
    all_workspaces = workspaces.get_workspace_names()
    for (workspace, _, map) in infos.keys():
        file_path = input_file.get_map_file(workspace, map)
        is_changed = False
        with open(file_path, 'r') as map_file:
            map_json_raw = json.load(map_file)
            map_json = input_file.unquote_urls(map_json_raw)
            for map_layer in map_json['layers']:
                layer_url = map_layer.get('url', None)
                if not layer_url:
                    continue
                match = re.match(gs_wms_url_pattern, layer_url)
                if not match:
                    continue
                layer_workspace = match.group(1)
                if not layer_workspace:
                    continue
                if layer_workspace not in all_workspaces:
                    logger.warning(f'      Do not know workspace {layer_workspace} in map {workspace}.{map}. Not migrating this url.')
                    continue

                layer_wms_workspace = wms.get_geoserver_workspace(layer_workspace)
                map_layer['url'] = f'{gs_url}{layer_wms_workspace}{match.group(2)}'
                is_changed = True
        if is_changed:
            logger.info(f'      Store new json for {workspace}.{map}')
            with open(file_path, 'w') as map_file:
                json.dump(map_json, map_file, indent=4)
    logger.info(f'    DONE - migrate maps json urls')


def migrate_metadata_records(workspace=None):
    logger.info(f'    Starting - migrate publication metadata records')
    infos = util.get_publication_infos(publ_type=LAYER_TYPE, workspace=workspace)
    for (workspace, _, layer) in infos.keys():
        wms.clear_cache(workspace)
        logger.info(f'      Migrate layer {workspace}.{layer}')
        try:
            muuid = layer_csw.patch_layer(workspace, layer, ['wms_url', 'graphic_url', 'identifier', 'layer_endpoint', ],
                                          create_if_not_exists=False, timeout=2)
            if not muuid:
                logger.warning(f'        Metadata record of layer was not migrated, because the record does not exist.')
        except requests.exceptions.ReadTimeout:
            md_props = list(layer_csw.get_metadata_comparison(workspace, layer).values())
            md_wms_url = md_props[0]['wms_url'] if md_props else None
            exp_wms_url = wms.add_capabilities_params_to_url(wms.get_wms_url(workspace, external_url=True))
            if md_wms_url != exp_wms_url:
                logger.exception(
                    f'        WMS URL was not migrated (should be {exp_wms_url}, but is {md_wms_url})!')
        time.sleep(0.5)

    infos = util.get_publication_infos(publ_type=MAP_TYPE, workspace=workspace)
    for (workspace, _, map) in infos.keys():
        logger.info(f'      Migrate map {workspace}.{map}')
        try:
            muuid = map_csw.patch_map(workspace, map, ['graphic_url', 'identifier', 'map_endpoint', 'map_file_endpoint', ],
                                      create_if_not_exists=False, timeout=2)
            if not muuid:
                logger.warning(f'        Metadata record of the map was not migrated, because the record does not exist.')
        except requests.exceptions.ReadTimeout:
            md_props = list(map_csw.get_metadata_comparison(workspace, map).values())
            md_map_endpoint = md_props[0]['map_endpoint'] if md_props else None
            exp_map_endpoint = util.url_for('rest_workspace_map.get', username=workspace, mapname=map)
            if md_map_endpoint != exp_map_endpoint:
                logger.exception(
                    f'        Map endpoint was not migrated (should be {exp_map_endpoint}, but is {md_map_endpoint})!')
        time.sleep(0.5)
    logger.info(f'    DONE - migrate publication metadata records')


def migrate_input_sld_directory_to_input_style():
    logger.info(f'    Starting - migrate input_sld directories to input_style')
    infos = util.get_publication_infos(publ_type=LAYER_TYPE)
    for (workspace, _, layer) in infos.keys():
        sld_path = os.path.join(layer_fs_util.get_layer_dir(workspace, layer),
                                'input_sld')
        if os.path.exists(sld_path):
            logger.info(f'      Migrate layer {workspace}.{layer}')
            style_path = input_style.get_layer_input_style_dir(workspace, layer)
            os.rename(sld_path, style_path)

    logger.info(f'    DONE - migrate input_sld directories to input_style')


def update_style_type_in_db():
    logger.info(f'    Starting - fulfill style type column in DB')
    db_schema = settings.LAYMAN_PRIME_SCHEMA

    update_layers = f"""update {db_schema}.publications set style_type = 'sld' where type = 'layman.layer'"""
    db_util.run_statement(update_layers)
    add_constraint = f"""DO $$ BEGIN
    alter table {db_schema}.publications add constraint con_style_type
check (type = 'layman.map' or style_type is not null);
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;"""
    db_util.run_statement(add_constraint)

    logger.info(f'    DONE - fulfill style type column in DB')
