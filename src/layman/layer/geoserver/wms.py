import requests
from urllib.parse import urljoin

from flask import current_app

from .util import get_gs_proxy_base_url
from layman import settings, patch_mode
from layman.cache import mem_redis
from layman.common import geoserver as common_geoserver
from layman.layer.util import is_layer_task_ready
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs, parse_qsl
from layman import util as layman_util
from layman.layer import LAYER_TYPE

FLASK_PROXY_KEY = f'{__name__}:PROXY:{{username}}'

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT
VERSION = '1.3.0'


def get_flask_proxy_key(username):
    return FLASK_PROXY_KEY.format(username=username)


def pre_publication_action_check(username, layername):
    pass


def post_layer(username, layername):
    pass


def patch_layer(workspace, layername, title, description, access_rights=None):
    geoserver_workspace = get_geoserver_workspace(workspace)
    common_geoserver.patch_feature_type(geoserver_workspace, layername, title, description, settings.LAYMAN_GS_AUTH)
    clear_cache(workspace)

    if access_rights and access_rights.get('read'):
        security_read_roles = common_geoserver.layman_users_to_geoserver_roles(access_rights['read'])
        common_geoserver.ensure_layer_security_roles(geoserver_workspace, layername, security_read_roles, 'r', settings.LAYMAN_GS_AUTH)

    if access_rights and access_rights.get('write'):
        security_write_roles = common_geoserver.layman_users_to_geoserver_roles(access_rights['write'])
        common_geoserver.ensure_layer_security_roles(geoserver_workspace, layername, security_write_roles, 'w', settings.LAYMAN_GS_AUTH)


def delete_layer(workspace, layername):
    geoserver_workspace = get_geoserver_workspace(workspace)
    common_geoserver.delete_feature_type(geoserver_workspace, layername, settings.LAYMAN_GS_AUTH)
    clear_cache(workspace)

    common_geoserver.delete_security_roles(f"{geoserver_workspace}.{layername}.r", settings.LAYMAN_GS_AUTH)
    common_geoserver.delete_security_roles(f"{geoserver_workspace}.{layername}.w", settings.LAYMAN_GS_AUTH)
    return {}


def get_wms_url(workspace, external_url=False):
    geoserver_workspace = get_geoserver_workspace(workspace)
    base_url = get_gs_proxy_base_url() if external_url else settings.LAYMAN_GS_URL
    return urljoin(base_url, geoserver_workspace + '/ows')


def get_wms_direct(username):
    headers = {
        settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE: settings.LAYMAN_GS_USER,
    }
    ows_url = get_wms_url(username)
    from .util import wms_direct
    key = get_flask_proxy_key(username)
    redis_obj = settings.LAYMAN_REDIS.hgetall(key)
    string_value = redis_obj['value'] if redis_obj is not None else None
    return wms_direct(ows_url, xml=string_value, headers=headers)


def get_wms_proxy(username):
    headers = {
        settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE: settings.LAYMAN_GS_USER,
    }
    key = get_flask_proxy_key(username)

    ows_url = get_wms_url(username)

    def create_string_value():
        r = requests.get(ows_url, params={
            'SERVICE': 'WMS',
            'REQUEST': 'GetCapabilities',
            'VERSION': VERSION,
        }, headers=headers, timeout=5,)
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
        from .util import wms_proxy
        wms_proxy = wms_proxy(ows_url, xml=string_value, headers=headers)
        return wms_proxy

    def currently_changing():
        layerinfos = layman_util.get_publication_infos(username, LAYER_TYPE)
        result = any((
            not is_layer_task_ready(username, layername)
            for (_, _, layername) in layerinfos
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
    wms_proxy_url = get_wms_url(username, external_url=True)

    if layername not in wms.contents:
        return {}
    return {
        'title': wms.contents[layername].title,
        'description': wms.contents[layername].abstract,
        'wms': {
            'url': wms_proxy_url
        },
    }


def get_publication_uuid(username, publication_type, publication_name):
    return None


def get_metadata_comparison(username, layername):
    wms = get_wms_direct(username)
    if wms is None:
        return {}
    cap_op = wms.getOperationByName('GetCapabilities')
    wms_url = next(
        (
            m.get("url")
            for m in (cap_op.methods if cap_op else [])
            if m.get("type").lower() == 'get'
        ), None
    )
    wms_layer = wms.contents.get(layername, None)
    try:
        title = wms_layer.title
    except BaseException:
        title = None
    try:
        abstract = wms_layer.abstract
    except BaseException:
        abstract = None
    try:
        extent = wms_layer.boundingBoxWGS84
    except BaseException:
        extent = None
    try:
        crs_list = sorted([
            int(crs.split(':')[-1]) for crs in wms_layer.crsOptions
            if crs.split(':')[0] == 'EPSG'
        ])
        reference_system = crs_list
    except Exception as e:
        current_app.logger.error(e)
        reference_system = None
    props = {
        'wms_url': wms_url,
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


def add_params_to_url(url, params):
    url_parts = list(urlparse(url))
    query = dict(parse_qsl(url_parts[4]))
    query.update(params)
    url_parts[4] = urlencode(query)
    url = urlunparse(url_parts)
    return url


def strip_params_from_url(url, params):
    params = [p.lower() for p in params]
    u = urlparse(url)
    query = parse_qs(u.query, keep_blank_values=True)
    for p in list(query.keys()):
        if p.lower() in params:
            query.pop(p, None)
    u = u._replace(query=urlencode(query, True))
    url = urlunparse(u)
    return url


def add_capabilities_params_to_url(url):
    params = {'SERVICE': 'WMS', 'REQUEST': 'GetCapabilities', 'VERSION': VERSION}
    url = add_params_to_url(url, params)
    return url


def get_capabilities_url(username):
    url = get_wms_url(username, external_url=True)
    url = add_capabilities_params_to_url(url)
    return url


def get_geoserver_workspace(workspace):
    return workspace + settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX


def get_qgis_store_name(layer):
    return f'{DEFAULT_WMS_STORE_PREFIX}_{layer}'
