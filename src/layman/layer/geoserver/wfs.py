import json
import traceback

import requests
from urllib.parse import urljoin

from flask import g, current_app

from . import headers_json
from layman.settings import *

FLASK_WFS_PROXY_KEY = 'layman.layer.geoserver.wfs_proxy'

def update_layer(username, layername, layerinfo):
    title = layerinfo['title']
    description = layerinfo['description']
    keywords = [
        "features",
        layername,
        title
    ]
    keywords = list(set(keywords))
    r = requests.put(
        urljoin(LAYMAN_GS_REST_WORKSPACES,
                username + '/datastores/postgresql/featuretypes/'+layername),
        data=json.dumps(
            {
                "featureType": {
                    "title": title,
                    "abstract": description,
                    "keywords": {
                        "string": keywords
                    },
                }
            }
        ),
        headers=headers_json,
        auth=LAYMAN_GS_AUTH
    )
    r.raise_for_status()
    g.pop(FLASK_WFS_PROXY_KEY, None)


def delete_layer(username, layername):
    info = get_layer_info(username, layername)
    if info:
        r = requests.delete(
            urljoin(LAYMAN_GS_REST_WORKSPACES,
                    username + '/datastores/postgresql/featuretypes/' + layername),
            headers=headers_json,
            auth=LAYMAN_GS_AUTH,
            params = {
                'recurse': 'true'
            }
        )
        r.raise_for_status()
        g.pop(FLASK_WFS_PROXY_KEY, None)
    return {}


def get_wfs_proxy(username):
    key = FLASK_WFS_PROXY_KEY
    if key not in g:
        wms_url = urljoin(LAYMAN_GS_URL, username + '/ows')
        from .util import wms_proxy
        wms_proxy = wms_proxy(wms_url)
        g.setdefault(key, wms_proxy)
    return g.get(key)


def get_layer_info(username, layername):
    try:
        wfs = get_wfs_proxy(username)
        wfs_proxy_url = urljoin(LAYMAN_GS_PROXY_URL, username + '/ows')

        return {
            'title': wfs.contents[layername].title,
            'description': wfs.contents[layername].abstract,
            'wfs': {
                'url': wfs_proxy_url
            },
        }
    except:
        return {}


def get_layer_names(username):
    try:
        wfs = get_wfs_proxy(username)

        return [*wfs.contents]
    except:
        return []