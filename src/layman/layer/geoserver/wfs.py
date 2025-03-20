from urllib.parse import urljoin
from flask import current_app

from geoserver import util as gs_util
from layman import settings, patch_mode
from layman.cache import mem_redis
from layman.common import geoserver as gs_common, empty_method
from layman.layer.geoserver import GEOSERVER_WFS_WORKSPACE, GeoserverIds
from layman.layer.util import is_layer_chain_ready
from layman import util as layman_util
from layman.layer import LAYER_TYPE
from layman.layer.layer_class import Layer
import requests_util.retry
from .util import get_gs_proxy_server_url, get_external_db_store_name, get_db_store_name, DEFAULT_INTERNAL_DB_STORE
from . import wms

FLASK_PROXY_KEY = f'{__name__}:PROXY:{{workspace}}'

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT
VERSION = gs_util.WFS_VERSION

pre_publication_action_check = empty_method
post_layer = empty_method


def get_flask_proxy_key():
    workspace = GEOSERVER_WFS_WORKSPACE
    return FLASK_PROXY_KEY.format(workspace=workspace)


def patch_layer(layer: Layer, *, title, description, original_data_source, access_rights=None):
    gs_layer_ids = layer.gs_ids.wfs
    if not get_layer_info_by_uuid(uuid=layer.uuid):
        return
    geodata_type = layer.geodata_type
    if geodata_type != settings.GEODATA_TYPE_VECTOR:
        raise NotImplementedError(f"Unknown geodata type: {geodata_type}")

    store_name = get_db_store_name(uuid=layer.uuid, original_data_source=original_data_source)
    gs_util.patch_feature_type(gs_layer_ids.workspace, gs_layer_ids.name, store_name=store_name, title=title, description=description, auth=settings.LAYMAN_GS_AUTH)
    clear_cache()

    if access_rights and access_rights.get('read'):
        security_read_roles = gs_common.layman_users_and_roles_to_geoserver_roles(access_rights['read'])
        gs_util.ensure_layer_security_roles(gs_layer_ids.workspace, gs_layer_ids.name, security_read_roles, 'r', settings.LAYMAN_GS_AUTH)

    if access_rights and access_rights.get('write'):
        security_write_roles = gs_common.layman_users_and_roles_to_geoserver_roles(access_rights['write'])
        gs_util.ensure_layer_security_roles(gs_layer_ids.workspace, gs_layer_ids.name, security_write_roles, 'w', settings.LAYMAN_GS_AUTH)


def delete_layer(layer: Layer):
    db_store_name = DEFAULT_INTERNAL_DB_STORE
    gs_layername = layer.gs_ids.wfs
    gs_util.delete_feature_type(gs_layername.workspace, gs_layername.name, settings.LAYMAN_GS_AUTH, store=db_store_name)
    gs_util.delete_feature_type(gs_layername.workspace, gs_layername.name, settings.LAYMAN_GS_AUTH, store=get_external_db_store_name(uuid=layer.uuid))
    gs_util.delete_db_store(gs_layername.workspace, settings.LAYMAN_GS_AUTH, store_name=get_external_db_store_name(uuid=layer.uuid))
    clear_cache()

    gs_util.delete_security_roles(f"{gs_layername.workspace}.{gs_layername.name}.r", settings.LAYMAN_GS_AUTH)
    gs_util.delete_security_roles(f"{gs_layername.workspace}.{gs_layername.name}.w", settings.LAYMAN_GS_AUTH)
    return {}


def get_wfs_url(external_url=False, *, x_forwarded_items=None):
    assert external_url or not x_forwarded_items
    workspace = GEOSERVER_WFS_WORKSPACE
    base_url = get_gs_proxy_server_url(x_forwarded_items=x_forwarded_items) + settings.LAYMAN_GS_PATH \
        if external_url else settings.LAYMAN_GS_URL
    return urljoin(base_url, workspace + '/wfs')


def get_wfs_direct():
    headers = {
        settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE: settings.LAYMAN_GS_USER,
    }
    ows_url = get_wfs_url()
    from geoserver.util import wfs_direct
    key = get_flask_proxy_key()
    redis_obj = settings.LAYMAN_REDIS.hgetall(key)
    string_value = redis_obj['value'] if redis_obj else None
    return wfs_direct(ows_url, xml=string_value, headers=headers)


def get_wfs_proxy():
    workspace = GEOSERVER_WFS_WORKSPACE
    headers = {
        settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE: settings.LAYMAN_GS_USER,
        'X-Forwarded-Proto': settings.LAYMAN_PUBLIC_URL_SCHEME,
        'X-Forwarded-Host': settings.LAYMAN_PROXY_SERVER_NAME,
        'X-Forwarded-Path': '',
    }
    key = get_flask_proxy_key()

    ows_url = get_wfs_url()

    def create_string_value():
        response = requests_util.retry.get_session().get(ows_url, params={
            'SERVICE': 'WFS',
            'REQUEST': 'GetCapabilities',
            'VERSION': VERSION,
        }, headers=headers, timeout=settings.DEFAULT_CONNECTION_TIMEOUT,)
        if response.status_code != 200:
            result = None
            if response.status_code != 404:
                response.raise_for_status()
                raise Exception(f'Status code = {response.status_code}')
        else:
            response.encoding = 'UTF-8'
            result = response.text
        return result

    def mem_value_from_string_value(string_value):
        from .util import wfs_proxy
        wfs_proxy = wfs_proxy(ows_url, xml=string_value, headers=headers)
        return wfs_proxy

    def currently_changing():
        layerinfos = layman_util.get_publication_infos(workspace, LAYER_TYPE)
        result = any((
            not is_layer_chain_ready(workspace, layername)
            for (_, _, layername) in layerinfos
        ))
        return result

    wfs_proxy = mem_redis.get(key, create_string_value, mem_value_from_string_value, currently_changing)

    return wfs_proxy


def clear_cache():
    key = get_flask_proxy_key()
    mem_redis.delete(key)


def get_layer_info(workspace, layername, *, x_forwarded_items=None):
    uuid = layman_util.get_publication_uuid(workspace, LAYER_TYPE, layername)
    return get_layer_info_by_uuid(uuid=uuid, x_forwarded_items=x_forwarded_items)


def get_layer_info_by_uuid(*, uuid, x_forwarded_items=None):
    gs_layername = GeoserverIds(uuid=uuid, ).wfs
    if uuid is None:
        return {}
    wfs_proxy_url = get_wfs_url(external_url=True, x_forwarded_items=x_forwarded_items)

    info = layman_util.get_publication_info_by_uuid(uuid, context={'keys': ['original_data_source']})
    original_data_source = info['original_data_source']
    data_store_name = get_db_store_name(uuid=uuid, original_data_source=original_data_source)
    feature_type = gs_util.get_feature_type(gs_layername.workspace, data_store_name, gs_layername.name)
    if not feature_type:
        return {}
    return {
        'title': feature_type['title'],
        'description': feature_type['abstract'] or None,
        'wfs': {
            'name': gs_layername.name,
            'url': wfs_proxy_url
        },
    }


def get_metadata_comparison(layer: Layer):
    gs_layername = layer.gs_ids.wfs
    if layer.geodata_type in (settings.GEODATA_TYPE_RASTER, settings.GEODATA_TYPE_UNKNOWN):
        return {}
    if layer.geodata_type != settings.GEODATA_TYPE_VECTOR:
        raise NotImplementedError(f"Unknown geodata type: {layer.geodata_type}")

    wfs = get_wfs_direct()
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
    wfs_layername = f"{gs_layername.workspace}:{gs_layername.name}"
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
    except BaseException as exception:
        current_app.logger.error(exception)
        reference_system = None
    props = {
        'wfs_url': wfs_url,
        'title': title,
        'abstract': abstract,
        'extent': extent,
        'reference_system': reference_system,
    }
    # current_app.logger.info(f"props:\n{json.dumps(props, indent=2)}")
    url = get_capabilities_url()
    return {
        f"{url}": props
    }


def add_capabilities_params_to_url(url):
    params = {'SERVICE': 'WFS', 'REQUEST': 'GetCapabilities', 'VERSION': VERSION}
    url = wms.add_params_to_url(url, params)
    return url


def get_capabilities_url():
    url = get_wfs_url(external_url=True)
    url = add_capabilities_params_to_url(url)
    return url
