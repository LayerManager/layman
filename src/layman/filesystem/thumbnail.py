import os
import glob
from urllib.parse import urljoin

from flask import url_for

from . import get_user_dir
from layman.settings import *


def get_layer_info(username, layername):
    thumbnail_path = get_layer_thumbnail_path(username, layername)
    if thumbnail_path is not None:
        return {
            'thumbnail': {
                'url': url_for('get_layer_thumbnail', username=username,
                               layername=layername)
            }
        }
    return {}


def update_layer(username, layername, layerinfo):
    pass


def delete_layer(username, layername):
    thumbnail_path = get_layer_thumbnail_path(username, layername)
    try:
        os.remove(thumbnail_path)
    except OSError:
        pass
    return {}


def get_layer_names(username):
    ending = '.thumbnail.png'
    userdir = get_user_dir(username)
    pattern = os.path.join(userdir, '*'+ending)
    filenames = glob.glob(pattern)
    layer_names = list(map(
        lambda fn: os.path.basename(fn)[:-len(ending)],
        filenames))
    return layer_names


def get_layer_thumbnail_path(username, layername):
    userdir = get_user_dir(username)
    thumbnail_path = os.path.join(userdir, layername+'.thumbnail.png')
    if os.path.exists(thumbnail_path):
        thumbnail_path = os.path.relpath(thumbnail_path, userdir)
        return thumbnail_path
    return None


def generate_layer_thumbnail(username, layername):
    wms_url = urljoin(LAYMAN_GS_URL, username + '/ows')
    userdir = get_user_dir(username)
    from layman.geoserver.util import wms_proxy
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
    tn_path = os.path.join(userdir, layername+'.thumbnail.png')
    out = open(tn_path, 'wb')
    out.write(tn_img.read())
    out.close()
    return tn_img