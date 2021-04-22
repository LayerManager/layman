import os
import pathlib

from layman import settings, LaymanError, patch_mode
from layman.util import url_for
from layman.common.filesystem import util as common_util
from . import util, input_file
from ..geoserver import wms as geoserver_wms

LAYER_SUBDIR = __name__.split('.')[-1]

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


def get_layer_thumbnail_dir(username, layername):
    thumbnail_dir = os.path.join(util.get_layer_dir(username, layername),
                                 'thumbnail')
    return thumbnail_dir


def ensure_layer_thumbnail_dir(username, layername):
    thumbnail_dir = get_layer_thumbnail_dir(username, layername)
    pathlib.Path(thumbnail_dir).mkdir(parents=True, exist_ok=True)
    return thumbnail_dir


def get_layer_info(username, layername):
    thumbnail_path = get_layer_thumbnail_path(username, layername)
    if os.path.exists(thumbnail_path):
        return {
            'thumbnail': {
                'url': url_for('rest_workspace_layer_thumbnail.get', workspace=username,
                               layername=layername),
                'path': os.path.relpath(thumbnail_path, common_util.get_user_dir(username))
            }
        }
    return {}


get_publication_uuid = input_file.get_publication_uuid


def pre_publication_action_check(username, layername):
    pass


def post_layer(username, layername):
    pass


def patch_layer(username, layername):
    pass


def delete_layer(username, layername):
    util.delete_layer_subdir(username, layername, LAYER_SUBDIR)


def get_layer_thumbnail_path(username, layername):
    thumbnail_dir = get_layer_thumbnail_dir(username, layername)
    return os.path.join(thumbnail_dir, layername + '.png')


def generate_layer_thumbnail(workspace, layername):
    headers = {
        settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE: settings.LAYMAN_GS_USER,
    }
    wms_url = geoserver_wms.get_wms_url(workspace)
    from layman.layer.geoserver.util import wms_proxy
    from layman.common.geoserver import get_layer_thumbnail, get_layer_square_bbox
    wms = wms_proxy(wms_url, headers=headers)
    # current_app.logger.info(list(wms.contents))
    tn_bbox = get_layer_square_bbox(wms, layername)
    # TODO https://github.com/geopython/OWSLib/issues/709
    # tn_img = wms.getmap(
    #     layers=[layername],
    #     srs='EPSG:3857',
    #     bbox=tn_bbox,
    #     size=(300, 300),
    #     format='image/png',
    #     transparent=True,
    # )
    ensure_layer_thumbnail_dir(workspace, layername)
    tn_path = get_layer_thumbnail_path(workspace, layername)
    # out = open(tn_path, 'wb')
    # out.write(tn_img.read())
    # out.close()

    from layman.layer.geoserver.wms import VERSION
    r = get_layer_thumbnail(wms_url, layername, tn_bbox, headers=headers, wms_version=VERSION)
    if "png" not in r.headers['content-type'].lower():
        raise LaymanError("Thumbnail rendering failed", data=r.content)
    r.raise_for_status()
    with open(tn_path, "wb") as out_file:
        out_file.write(r.content)


def get_metadata_comparison(username, layername):
    pass
