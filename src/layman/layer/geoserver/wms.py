import json
import traceback

import requests
from urllib.parse import urljoin

from flask import g, current_app

from . import headers_json
from .util import get_gs_proxy_base_url
from layman import settings


FLASK_PROXY_KEY = f'{__name__}:PROXY:{{username}}'


def get_flask_proxy_key(username):
    return FLASK_PROXY_KEY.format(username=username)


def update_layer(username, layername, layerinfo):
    g.pop(get_flask_proxy_key(username), None)
    pass


def delete_layer(username, layername):
    info = get_layer_info(username, layername)
    if info:
        r = requests.delete(
            urljoin(settings.LAYMAN_GS_REST_WORKSPACES, username +
                    '/layers/' + layername),
            headers=headers_json,
            auth=settings.LAYMAN_GS_AUTH,
            params = {
                'recurse': 'true'
            }
        )
        # app.logger.info(r.text)
        r.raise_for_status()
        g.pop(get_flask_proxy_key(username), None)
    return {}


def get_wms_proxy(username):
    key = get_flask_proxy_key(username)
    if key not in g:
        wms_url = urljoin(settings.LAYMAN_GS_URL, username + '/ows')
        from .util import wms_proxy
        wms_proxy = wms_proxy(wms_url)
        g.setdefault(key, wms_proxy)
    return g.get(key)

def get_layer_info(username, layername):

    try:
        wms = get_wms_proxy(username)
        wms_proxy_url = urljoin(get_gs_proxy_base_url(), username + '/ows')

        return {
            'title': wms.contents[layername].title,
            'description': wms.contents[layername].abstract,
            'wms': {
                'url': wms_proxy_url
            },
        }
    except:
        return {}


def get_layer_names(username):
    try:
        wms = get_wms_proxy(username)

        return [*wms.contents]
    except:
        return []


def get_publication_names(username, publication_type):
    if publication_type != '.'.join(__name__.split('.')[:-2]):
        raise Exception(f'Unknown pyblication type {publication_type}')

    return get_layer_names(username)


def get_publication_uuid(username, publication_type, publication_name):
    return None


