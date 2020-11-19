import os
import pathlib
import requests
from urllib.parse import urljoin
from layman import settings
from flask import current_app

from layman import patch_mode
from layman.util import url_for
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


get_publication_infos = input_file.get_publication_infos

get_publication_uuid = input_file.get_publication_uuid


def post_layer(username, layername):
    pass


def patch_layer(username, layername):
    pass


def delete_layer(username, layername):
    util.delete_layer_subdir(username, layername, LAYER_SUBDIR)


get_layer_infos = input_file.get_layer_infos


def get_layer_thumbnail_path(username, layername):
    thumbnail_dir = get_layer_thumbnail_dir(username, layername)
    return os.path.join(thumbnail_dir, layername + '.png')


def generate_layer_thumbnail(username, layername):
    headers = {
        settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE: settings.LAYMAN_GS_USER,
    }
    wms_url = urljoin(settings.LAYMAN_GS_URL, username + '/ows')
    from layman.layer.geoserver.util import wms_proxy
    wms = wms_proxy(wms_url, headers=headers)
    # current_app.logger.info(list(wms.contents))
    bbox = list(next(t for t in wms[layername].crs_list if t[4].lower() == 'epsg:3857'))
    # current_app.logger.info(f"bbox={bbox}")
    min_range = min(bbox[2] - bbox[0], bbox[3] - bbox[1]) / 2
    tn_bbox = (
        (bbox[0] + bbox[2]) / 2 - min_range,
        (bbox[1] + bbox[3]) / 2 - min_range,
        (bbox[0] + bbox[2]) / 2 + min_range,
        (bbox[1] + bbox[3]) / 2 + min_range,
    )
    # TODO https://github.com/geopython/OWSLib/issues/709
    # tn_img = wms.getmap(
    #     layers=[layername],
    #     srs='EPSG:3857',
    #     bbox=tn_bbox,
    #     size=(300, 300),
    #     format='image/png',
    #     transparent=True,
    # )
    ensure_layer_thumbnail_dir(username, layername)
    tn_path = get_layer_thumbnail_path(username, layername)
    # out = open(tn_path, 'wb')
    # out.write(tn_img.read())
    # out.close()

    from layman.layer.geoserver.wms import VERSION
    r = requests.get(wms_url, params={
        'SERVICE': 'WMS',
        'REQUEST': 'GetMap',
        'VERSION': VERSION,
        'LAYERS': layername,
        'CRS': 'EPSG:3857',
        'BBOX': ','.join([str(c) for c in tn_bbox]),
        'WIDTH': 300,
        'HEIGHT': 300,
        'FORMAT': 'image/png',
        'TRANSPARENT': 'TRUE',
    }, headers=headers)
    r.raise_for_status()
    with open(tn_path, "wb") as out_file:
        out_file.write(r.content)


def get_metadata_comparison(username, layername):
    pass
