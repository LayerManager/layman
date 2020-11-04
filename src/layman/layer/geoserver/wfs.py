import json
import traceback

import requests
from urllib.parse import urljoin

from flask import g, current_app

from .util import get_gs_proxy_base_url
from . import headers_json
from . import wms
from layman import settings, patch_mode
from layman.cache import mem_redis
from layman.layer.filesystem import input_file
from layman.layer.util import is_layer_task_ready
from layman.common import geoserver as common_geoserver

FLASK_PROXY_KEY = f'{__name__}:PROXY:{{username}}'

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT
VERSION = '2.0.0'


def get_flask_proxy_key(username):
    return FLASK_PROXY_KEY.format(username=username)


def post_layer(username, layername):
    pass


def patch_layer(username, layername, title, description):
    keywords = [
        "features",
        layername,
        title
    ]
    keywords = list(set(keywords))
    ftype = {
        "title": title,
        "abstract": description,
        "keywords": {
            "string": keywords
        },
    }
    ftype = {k: v for k, v in ftype.items() if v is not None}
    body = {
        "featureType": ftype
    }
    r = requests.put(
        urljoin(settings.LAYMAN_GS_REST_WORKSPACES,
                username + '/datastores/postgresql/featuretypes/' + layername),
        data=json.dumps(body),
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
        params={
            'recurse': 'true'
        }
    )
    if r.status_code != 404:
        r.raise_for_status()
    clear_cache(username)
    wms.clear_cache(username)

    common_geoserver.delete_security_roles(f"{username}.{layername}.r", settings.LAYMAN_GS_AUTH)
    common_geoserver.delete_security_roles(f"{username}.{layername}.w", settings.LAYMAN_GS_AUTH)
    return {}


def get_wfs_url(username):
    return urljoin(settings.LAYMAN_GS_URL, username + '/wfs')


def get_wfs_direct(username):
    ows_url = get_wfs_url(username)
    from .util import wfs_direct
    key = get_flask_proxy_key(username)
    redis_obj = settings.LAYMAN_REDIS.hgetall(key)
    string_value = redis_obj['value'] if redis_obj is not None else None
    return wfs_direct(ows_url, xml=string_value)


def get_wfs_proxy(username):
    key = get_flask_proxy_key(username)

    ows_url = get_wfs_url(username)

    def create_string_value():
        r = requests.get(ows_url, params={
            'SERVICE': 'WFS',
            'REQUEST': 'GetCapabilities',
            'VERSION': VERSION,
        })
        if r.status_code != 200:
            result = None
            if r.status_code != 404:
                r.raise_for_status()
                raise Exception(f'Status code = {r.status_code}')
        else:
            r.encoding = 'UTF-8'
            result = r.text
        return result

    def mem_value_from_string_value(string_value):
        from .util import wfs_proxy
        wfs_proxy = wfs_proxy(ows_url, xml=string_value)
        return wfs_proxy

    def currently_changing():
        layerinfos = input_file.get_layer_infos(username)
        result = any((
            not is_layer_task_ready(username, layername)
            for layername in layerinfos
        ))
        return result

    wfs_proxy = mem_redis.get(key, create_string_value, mem_value_from_string_value, currently_changing)

    return wfs_proxy


def clear_cache(username):
    key = get_flask_proxy_key(username)
    mem_redis.delete(key)


def _get_wfs_proxy_url(username):
    return urljoin(get_gs_proxy_base_url(), username + '/wfs')


def get_layer_info(username, layername):
    wfs = get_wfs_proxy(username)
    if wfs is None:
        return {}
    wfs_proxy_url = _get_wfs_proxy_url(username)

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


def get_layer_infos(username):
    wfs = get_wfs_proxy(username)
    if wfs is None:
        result = {}
    else:
        result = {name.split(':')[1]: {"name": name.split(':')[1],
                                       "title": info.title} for (name, info) in wfs.contents.items()}
    return result


def get_publication_infos(username, publication_type):
    if publication_type != '.'.join(__name__.split('.')[:-2]):
        raise Exception(f'Unknown pyblication type {publication_type}')

    infos = get_layer_infos(username)
    return infos


def get_publication_uuid(username, publication_type, publication_name):
    return None


def get_metadata_comparison(username, layername):
    wfs = get_wfs_direct(username)
    if wfs is None:
        return {}
    cap_op = wfs.getOperationByName('GetCapabilities')
    wfs_url = next(
        (
            m.get("url")
            for m in (cap_op.methods if cap_op else [])
            if m.get("type").lower() == 'get'
        ), None
    )
    wfs_layername = f"{username}:{layername}"
    wfs_layer = wfs.contents.get(wfs_layername, None)
    try:
        title = wfs_layer.title
    except BaseException:
        title = None
    try:
        abstract = wfs_layer.abstract
    except BaseException:
        abstract = None
    try:
        extent = wfs_layer.boundingBox[:-1]
    except BaseException:
        extent = None
    try:
        crs_list = [int(crs.getcode().split(':')[-1]) for crs in wfs_layer.crsOptions]
        crs_list.append(4326)
        crs_list = sorted(list(set(crs_list)))
        reference_system = crs_list
    except Exception as e:
        current_app.logger.error(e)
        reference_system = None
    props = {
        'wfs_url': wfs_url,
        'title': title,
        'abstract': abstract,
        'extent': extent,
        'reference_system': reference_system,
    }
    # current_app.logger.info(f"props:\n{json.dumps(props, indent=2)}")
    url = get_capabilities_url(username)
    return {
        f"{url}": props
    }


def add_capabilities_params_to_url(url):
    params = {'SERVICE': 'WFS', 'REQUEST': 'GetCapabilities', 'VERSION': VERSION}
    url = wms.add_params_to_url(url, params)
    return url


def get_capabilities_url(username):
    url = _get_wfs_proxy_url(username)
    url = add_capabilities_params_to_url(url)
    return url
