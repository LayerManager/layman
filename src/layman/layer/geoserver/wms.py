import json
import traceback

import requests
from urllib.parse import urljoin

from flask import g, current_app

from . import headers_json
from .util import get_gs_proxy_base_url
from layman import settings
from layman.cache import mem_redis


FLASK_PROXY_KEY = f'{__name__}:PROXY:{{username}}'


def get_flask_proxy_key(username):
    return FLASK_PROXY_KEY.format(username=username)


def update_layer(username, layername, layerinfo):
    clear_cache(username)
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
        r.raise_for_status()
        return r.text

    def mem_value_from_string_value(string_value):
        from .util import wms_proxy
        wms_proxy = wms_proxy(ows_url, xml=string_value)
        return wms_proxy

    wms_proxy = mem_redis.get(key, create_string_value, mem_value_from_string_value)
    return wms_proxy


def clear_cache(username):
    key = get_flask_proxy_key(username)
    mem_redis.delete(key)


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
        current_app.logger.info('Exception during WMS.get_layer_info')
        # traceback.print_exc()
        return {}


def get_layer_names(username):
    try:
        wms = get_wms_proxy(username)

        return [*wms.contents]
    except:
        # TODO remove except:, handle raise_for_status in better way
        current_app.logger.info('Exception during WMS.get_layer_names')
        # traceback.print_exc()
        return []


def get_publication_names(username, publication_type):
    if publication_type != '.'.join(__name__.split('.')[:-2]):
        raise Exception(f'Unknown publication type {publication_type}')

    return get_layer_names(username)


def get_publication_uuid(username, publication_type, publication_name):
    return None


