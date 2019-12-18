import os
import pathlib
from urllib.parse import urljoin
from layman import settings
from flask import url_for

from layman import patch_mode
from . import util
from layman.common.filesystem import util as common_util
from . import input_file


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
                'url': url_for('rest_layer_thumbnail.get', username=username,
                               layername=layername),
                'path': os.path.relpath(thumbnail_path, common_util.get_user_dir(username))
            }
        }
    return {}


update_layer = input_file.update_layer


get_publication_names = input_file.get_publication_names


get_publication_uuid = input_file.get_publication_uuid


def delete_layer(username, layername):
    util.delete_layer_subdir(username, layername, LAYER_SUBDIR)


get_layer_names = input_file.get_layer_names


def get_layer_thumbnail_path(username, layername):
    thumbnail_dir = get_layer_thumbnail_dir(username, layername)
    return os.path.join(thumbnail_dir, layername+'.png')


def generate_layer_thumbnail(username, layername):
    wms_url = urljoin(settings.LAYMAN_GS_URL, username + '/ows')
    from layman.layer.geoserver.util import wms_proxy
    wms = wms_proxy(wms_url)
    # app.logger.info(list(wms.contents))
    bbox = list(wms[layername].boundingBox)
    # app.logger.info(bbox)
    min_range = min(bbox[2] - bbox[0], bbox[3] - bbox[1]) / 2
    tn_bbox = (
        (bbox[0] + bbox[2]) / 2 - min_range,
        (bbox[1] + bbox[3]) / 2 - min_range,
        (bbox[0] + bbox[2]) / 2 + min_range,
        (bbox[1] + bbox[3]) / 2 + min_range,
    )
    tn_img = wms.getmap(
        layers=[layername],
        srs='EPSG:3857',
        bbox=tn_bbox,
        size=(300, 300),
        format='image/png',
        transparent=True,
    )
    ensure_layer_thumbnail_dir(username, layername)
    tn_path = get_layer_thumbnail_path(username, layername)
    out = open(tn_path, 'wb')
    out.write(tn_img.read())
    out.close()
    return tn_img