import json
import traceback

import requests
from urllib.parse import urljoin

from flask import g, current_app

from . import headers_json
from .util import get_gs_proxy_base_url
from layman import settings
from layman.cache import mem_redis
from layman.layer.filesystem import input_file
from layman.layer.util import is_layer_task_ready


FLASK_PROXY_KEY = f'{__name__}:PROXY:{{username}}'


def get_flask_proxy_key(username):
    return FLASK_PROXY_KEY.format(username=username)


def update_layer(username, layername, layerinfo):
    clear_cache(username)
    pass


def delete_layer(username, layername):
    r = requests.delete(
        urljoin(settings.LAYMAN_GS_REST_WORKSPACES, username +
                '/layers/' + layername),
        headers=headers_json,
        auth=settings.LAYMAN_GS_AUTH,
        params = {
            'recurse': 'true'
        }
    )
    if r.status_code != 404:
        r.raise_for_status()
    clear_cache(username)
    return {}


def get_wms_proxy(username):
    key = get_flask_proxy_key(username)

    ows_url = urljoin(settings.LAYMAN_GS_URL, username + '/ows')
    def create_string_value():
        r = requests.get(ows_url, params={
            'SERVICE': 'WMS',
            'REQUEST': 'GetCapabilities',
            'VERSION': '1.1.1',
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
        from .util import wms_proxy
        wms_proxy = wms_proxy(ows_url, xml=string_value)
        return wms_proxy

    def currently_changing():
        layernames = input_file.get_layer_names(username)
        result = any((
            not is_layer_task_ready(username, layername)
            for layername in layernames
        ))
        return result

    wms_proxy = mem_redis.get(key, create_string_value, mem_value_from_string_value, currently_changing)
    return wms_proxy


def clear_cache(username):
    key = get_flask_proxy_key(username)
    mem_redis.delete(key)


def get_layer_info(username, layername):
    wms = get_wms_proxy(username)
    if wms is None:
        return {}
    wms_proxy_url = urljoin(get_gs_proxy_base_url(), username + '/ows')

    if layername not in wms.contents:
        return {}
    return {
        'title': wms.contents[layername].title,
        'description': wms.contents[layername].abstract,
        'wms': {
            'url': wms_proxy_url
        },
    }


def get_layer_names(username):
    wms = get_wms_proxy(username)
    if wms is None:
        result = []
    else:
        result = [*wms.contents]

    return result


def get_publication_names(username, publication_type):
    if publication_type != '.'.join(__name__.split('.')[:-2]):
        raise Exception(f'Unknown publication type {publication_type}')

    return get_layer_names(username)


def get_publication_uuid(username, publication_type, publication_name):
    return None


