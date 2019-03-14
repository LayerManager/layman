import json
import traceback

import requests
from urllib.parse import urljoin

from flask import g, current_app

from .util import get_gs_proxy_base_url
from . import headers_json
from layman import settings

FLASK_PROXY_KEY = f'{__name__}:PROXY:{{username}}'


def get_flask_proxy_key(username):
    return FLASK_PROXY_KEY.format(username=username)


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
        urljoin(settings.LAYMAN_GS_REST_WORKSPACES,
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
        auth=settings.LAYMAN_GS_AUTH
    )
    r.raise_for_status()
    g.pop(get_flask_proxy_key(username), None)


def delete_layer(username, layername):
    info = get_layer_info(username, layername)
    if info:
        r = requests.delete(
            urljoin(settings.LAYMAN_GS_REST_WORKSPACES,
                    username + '/datastores/postgresql/featuretypes/' + layername),
            headers=headers_json,
            auth=settings.LAYMAN_GS_AUTH,
            params = {
                'recurse': 'true'
            }
        )
        r.raise_for_status()
        g.pop(get_flask_proxy_key(username), None)
    return {}


def get_wfs_proxy(username):
    key = get_flask_proxy_key(username)
    if key not in g:
        wms_url = urljoin(settings.LAYMAN_GS_URL, username + '/ows')
        from .util import wms_proxy
        wms_proxy = wms_proxy(wms_url)
        g.setdefault(key, wms_proxy)
    return g.get(key)


def get_layer_info(username, layername):
    try:
        wfs = get_wfs_proxy(username)
        wfs_proxy_url = urljoin(get_gs_proxy_base_url(), username + '/ows')

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


def get_publication_names(username, publication_type):
    if publication_type != '.'.join(__name__.split('.')[:-2]):
        raise Exception(f'Unknown pyblication type {publication_type}')

    return get_layer_names(username)


def get_publication_uuid(username, publication_type, publication_name):
    return None
