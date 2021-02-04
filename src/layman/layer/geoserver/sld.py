from layman.layer.filesystem.input_sld import get_layer_file
from layman.common import geoserver
from layman import settings, patch_mode
from . import wms
from ...util import url_for

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


def get_workspace_style_url(workspace, style=None):
    geoserver_workspace = wms.get_geoserver_workspace(workspace)
    return geoserver.get_workspace_style_url(geoserver_workspace, style)


def get_workspace_layer_url(workspace, layer=None):
    geoserver_workspace = wms.get_geoserver_workspace(workspace)
    return geoserver.get_workspace_layer_url(geoserver_workspace, layer)


def pre_publication_action_check(username, layername):
    pass


def post_layer(username, layername):
    pass


def patch_layer(username, layername):
    pass


def delete_layer(workspace, layername):
    geoserver_workspace = wms.get_geoserver_workspace(workspace)
    sld_stream = geoserver.delete_workspace_style(geoserver_workspace, layername, auth=settings.LAYMAN_GS_AUTH)
    wms.clear_cache(workspace)
    if sld_stream == {}:
        return {}
    else:
        return {
            'sld': {
                'file': sld_stream,
            }
        }


def get_layer_info(username, layername):
    r = get_style_response(username, layername, geoserver.headers_sld, settings.LAYMAN_GS_AUTH)
    if r.status_code == 200:
        url = url_for('rest_layer_style.get', username=username, layername=layername)
        info = {
            'sld': {
                'url': url
            },
        }
    else:
        info = {}

    return info


def get_publication_uuid(username, publication_type, publication_name):
    return None


def create_layer_style(workspace, layername):
    geoserver_workspace = wms.get_geoserver_workspace(workspace)
    sld_file = get_layer_file(workspace, layername)
    # print('create_layer_style', sld_file)
    geoserver.post_workspace_sld_style(geoserver_workspace, layername, sld_file)


def get_metadata_comparison(username, layername):
    pass


def get_style_response(workspace, stylename, headers=None, auth=None):
    geoserver_workspace = wms.get_geoserver_workspace(workspace)
    return geoserver.get_workspace_style_response(geoserver_workspace, stylename, headers, auth)
