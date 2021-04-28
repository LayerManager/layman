from geoserver import util as gs_util
from layman import settings, patch_mode
from layman.common import empty_method, empty_method_returns_none, empty_method_returns_dict
from layman.common.db import launder_attribute_name
from layman.layer.filesystem import input_style
from . import wms
from ...util import url_for

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT

get_metadata_comparison = empty_method_returns_dict
pre_publication_action_check = empty_method
post_layer = empty_method
patch_layer = empty_method
get_publication_uuid = empty_method_returns_none


def get_workspace_style_url(workspace, style=None):
    geoserver_workspace = wms.get_geoserver_workspace(workspace)
    return gs_util.get_workspace_style_url(geoserver_workspace, style)


def delete_layer(workspace, layername):
    geoserver_workspace = wms.get_geoserver_workspace(workspace)
    sld_stream = gs_util.delete_workspace_style(geoserver_workspace, layername, auth=settings.LAYMAN_GS_AUTH)
    wms.clear_cache(workspace)
    if sld_stream:
        result = {
            'style': {
                'file': sld_stream,
            }
        }
    else:
        result = {}
    return result


def get_layer_info(workspace, layername):
    r = get_style_response(workspace, layername, gs_util.headers_sld, settings.LAYMAN_GS_AUTH)
    if r.status_code == 200:
        url = url_for('rest_workspace_layer_style.get', workspace=workspace, layername=layername)
        info = {
            'style': {
                'url': url,
                'type': 'sld',
            },
        }
    else:
        info = {}

    return info


def create_layer_style(workspace, layername):
    geoserver_workspace = wms.get_geoserver_workspace(workspace)
    style_file = input_style.get_layer_file(workspace, layername)
    gs_util.post_workspace_sld_style(geoserver_workspace, layername, style_file, launder_attribute_name)
    wms.clear_cache(workspace)


def get_style_response(workspace, stylename, headers=None, auth=None):
    geoserver_workspace = wms.get_geoserver_workspace(workspace)
    return gs_util.get_workspace_style_response(geoserver_workspace, stylename, headers, auth)
