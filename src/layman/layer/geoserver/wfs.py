import json
import traceback

import requests
from urllib.parse import urljoin

from flask import g, current_app

from .util import get_gs_proxy_base_url
from . import headers_json
from . import wms
from layman import settings
from layman.cache import mem_redis

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
    clear_cache(username)
    wms.clear_cache(username)


def delete_layer(username, layername):
    r = requests.delete(
        urljoin(settings.LAYMAN_GS_REST_WORKSPACES,
                username + '/datastores/postgresql/featuretypes/' + layername),
        headers=headers_json,
        auth=settings.LAYMAN_GS_AUTH,
        params = {
            'recurse': 'true'
        }
    )
    if r.status_code != 404:
        r.raise_for_status()
    clear_cache(username)
    wms.clear_cache(username)
    return {}


def get_wfs_proxy(username):
    key = get_flask_proxy_key(username)

    ows_url = urljoin(settings.LAYMAN_GS_URL, username + '/ows')
    def create_string_value():
        r = requests.get(ows_url, params={
            'SERVICE': 'WFS',
            'REQUEST': 'GetCapabilities',
            'VERSION': '1.0.0',
        })
        if r.status_code != 200:
            result = None
            if r.status_code != 404:
                r.raise_for_status()
                raise Exception(f'Status code = {r.status_code}')
        else:
            result = r.text
        return result

    def mem_value_from_string_value(string_value):
        from .util import wfs_proxy
        wfs_proxy = wfs_proxy(ows_url, xml=string_value)
        return wfs_proxy

    def currently_changing():
        from layman.celery import is_task_running
        from .tasks import PUBLISH_LAYER_FROM_DB_NAME
        result = is_task_running(PUBLISH_LAYER_FROM_DB_NAME, username)
        return result

    wfs_proxy = mem_redis.get(key, create_string_value, mem_value_from_string_value, currently_changing)

    return wfs_proxy


def clear_cache(username):
    key = get_flask_proxy_key(username)
    mem_redis.delete(key)


def get_layer_info(username, layername):
    wfs = get_wfs_proxy(username)
    if wfs is None:
        return {}
    wfs_proxy_url = urljoin(get_gs_proxy_base_url(), username + '/ows')

    wfs_layername = f"{username}:{layername}"
    if wfs_layername not in wfs.contents:
        return {}
    return {
        'title': wfs.contents[wfs_layername].title,
        'description': wfs.contents[wfs_layername].abstract,
        'wfs': {
            'url': wfs_proxy_url
        },
    }


def get_layer_names(username):
    wfs = get_wfs_proxy(username)
    if wfs is None:
        result = []
    else:
        result = [
            wfs_layername.split(':')[1]
            for wfs_layername in [*wfs.contents]
        ]
    return result


def get_publication_names(username, publication_type):
    if publication_type != '.'.join(__name__.split('.')[:-2]):
        raise Exception(f'Unknown pyblication type {publication_type}')

    return get_layer_names(username)


def get_publication_uuid(username, publication_type, publication_name):
    return None
