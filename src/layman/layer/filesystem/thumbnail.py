import os
import pathlib

from geoserver import util as gs_util
from layman import settings, LaymanError, patch_mode
from layman.util import url_for, get_publication_info_by_uuid
from layman.common import empty_method, empty_method_returns_dict, bbox as bbox_util
from layman.common.filesystem import util as common_util
from . import util, input_file
from .. import LAYER_TYPE

LAYER_SUBDIR = __name__.rsplit('.', maxsplit=1)[-1]

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT

get_metadata_comparison = empty_method_returns_dict
pre_publication_action_check = empty_method
post_layer = empty_method
patch_layer = empty_method


def get_layer_thumbnail_dir(workspace, layername):
    thumbnail_dir = os.path.join(util.get_layer_dir(workspace, layername),
                                 'thumbnail')
    return thumbnail_dir


def ensure_layer_thumbnail_dir(workspace, layername):
    thumbnail_dir = get_layer_thumbnail_dir(workspace, layername)
    pathlib.Path(thumbnail_dir).mkdir(parents=True, exist_ok=True)
    return thumbnail_dir


def get_layer_info(workspace, layername, *, x_forwarded_items=None):
    thumbnail_path = get_layer_thumbnail_path(workspace, layername)
    if os.path.exists(thumbnail_path):
        return {
            'thumbnail': {
                'url': url_for('rest_workspace_layer_thumbnail.get', workspace=workspace,
                               layername=layername,
                               x_forwarded_items=x_forwarded_items),
                'path': os.path.relpath(thumbnail_path, common_util.get_workspace_dir(workspace))
            },
            '_thumbnail': {
                'path': thumbnail_path,
            },
        }
    return {}


get_publication_uuid = input_file.get_publication_uuid


def delete_layer(workspace, layername):
    util.delete_layer_subdir(workspace, layername, LAYER_SUBDIR)


def get_layer_thumbnail_path(workspace, layername):
    thumbnail_dir = get_layer_thumbnail_dir(workspace, layername)
    return os.path.join(thumbnail_dir, layername + '.png')


def generate_layer_thumbnail(workspace, layername, *, uuid=None):
    uuid = uuid or get_publication_uuid(workspace, LAYER_TYPE, layername)
    headers = {
        settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE: settings.LAYMAN_GS_USER,
    }
    layer_info = get_publication_info_by_uuid(uuid, context={'keys': ['wms', 'native_bounding_box', 'native_crs', ]})
    wms_url = layer_info['_wms']['url']
    native_bbox = layer_info['native_bounding_box']
    native_crs = layer_info['native_crs']
    gs_layername = layer_info['wms']['name']
    bbox = bbox_util.get_bbox_to_publish(native_bbox, native_crs)
    tn_bbox = gs_util.get_square_bbox(bbox)
    ensure_layer_thumbnail_dir(workspace, layername)
    tn_path = get_layer_thumbnail_path(workspace, layername)

    from layman.layer.geoserver.wms import VERSION
    response = gs_util.get_layer_thumbnail(wms_url, gs_layername, tn_bbox, native_crs, headers=headers, wms_version=VERSION)
    if "png" not in response.headers['content-type'].lower():
        raise LaymanError("Thumbnail rendering failed", data=response.content)
    response.raise_for_status()
    with open(tn_path, "wb") as out_file:
        out_file.write(response.content)
