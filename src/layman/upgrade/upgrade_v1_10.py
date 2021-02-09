import io
import json
import logging
import re
import time
import os
from layman import settings
from layman.http import LaymanError
from layman.common import prime_db_schema
from layman.common import geoserver as gs_common
from layman.common.prime_db_schema import workspaces
from layman import util
from layman.layer import LAYER_TYPE
from layman.layer import geoserver
from layman.layer.geoserver import wms
from layman.layer.micka import csw
from layman.layer.filesystem import util as layer_fs_util, input_style
from layman.map import MAP_TYPE
from layman.map.filesystem import input_file
from layman.layer.geoserver import util as gs_util

logger = logging.getLogger(__name__)


def check_usernames_for_wms_suffix():
    logger.info(f'    Starting - checking users with {settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX} suffix')
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
    logger.info(f'    DONE - checking users with {settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX} suffix')


def migrate_layers_to_wms_workspace(workspace=None):
    logger.info(f'    Starting - migrate layers to WMS workspace')
    infos = util.get_publication_infos(publ_type=LAYER_TYPE, workspace=workspace)
    for (workspace, publication_type, layer) in infos.keys():
        logger.info(f'      Migrate layer {workspace}.{layer}')
        info = util.get_publication_info(workspace, publication_type, layer)
        geoserver_workspace = wms.get_geoserver_workspace(workspace)
        geoserver.ensure_workspace(workspace)

        geoserver.publish_layer_from_db(workspace,
                                        layer,
                                        info.get('description'),
                                        info.get('title'),
                                        info.get('access_rights'),
                                        geoserver_workspace=geoserver_workspace)
        wms.clear_cache(workspace)

        sld_r = gs_common.get_workspace_style_response(workspace, layer, auth=settings.LAYMAN_GS_AUTH)
        sld_stream = io.BytesIO(sld_r.content)
        gs_common.post_workspace_sld_style(geoserver_workspace, layer, sld_stream)
        wms.clear_cache(workspace)

        gs_common.delete_workspace_style(workspace, layer, auth=settings.LAYMAN_GS_AUTH)
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
    logger.info(f'    Starting - migrate layer metadata records')
    infos = util.get_publication_infos(publ_type=LAYER_TYPE, workspace=workspace)
    for (workspace, _, layer) in infos.keys():
        wms.clear_cache(workspace)
        muuid = csw.patch_layer(workspace, layer, ['wms_url'], create_if_not_exists=False)
        if not muuid:
            logger.warning(f'      Metadata record of layer {workspace}.{layer} was not migrated, because the record does not exist.')
        time.sleep(0.5)
    logger.info(f'    DONE - migrate layer metadata records')


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
