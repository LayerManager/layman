import configparser
from urllib.parse import urljoin
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs, parse_qsl
import itertools
import logging
import os
from flask import current_app

import layman.layer.geoserver
from geoserver import util as gs_util
from layman import settings, patch_mode, util as layman_util
from layman.cache import mem_redis
from layman.common import geoserver as gs_common, empty_method
from layman.layer.util import is_layer_chain_ready
from layman.layer import LAYER_TYPE
from layman.layer.filesystem import gdal
from layman.layer.layer_class import Layer
import requests_util.retry
from . import GeoserverIds
from .util import get_gs_proxy_server_url, get_external_db_store_name, image_mosaic_granules_to_wms_time_key, \
    get_db_store_name, DEFAULT_INTERNAL_DB_STORE

FLASK_PROXY_KEY = f'{__name__}:PROXY:{{workspace}}'
DEFAULT_WMS_QGIS_STORE_PREFIX = 'qgis'
DEFAULT_GEOTIFF_STORE_PREFIX = 'geotiff'
DEFAULT_IMAGE_MOSAIC_STORE_PREFIX = 'image_mosaic'

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT
VERSION = gs_util.WMS_VERSION
logger = logging.getLogger(__name__)

pre_publication_action_check = empty_method
post_layer = empty_method


def get_flask_proxy_key():
    workspace = layman.layer.geoserver.GEOSERVER_WMS_WORKSPACE
    return FLASK_PROXY_KEY.format(workspace=workspace)


def patch_layer(layer: Layer):
    gs_layer_ids = layer.gs_ids.wms
    if not get_layer_info_by_uuid(uuid=layer.uuid):
        return
    geodata_type = layer.geodata_type
    if geodata_type == settings.GEODATA_TYPE_VECTOR:
        if layer.style_type == 'sld':
            store_name = get_db_store_name(uuid=layer.uuid, original_data_source=layer.original_data_source.value)
            gs_util.patch_feature_type(gs_layer_ids.workspace, gs_layer_ids.name, store_name=store_name, title=layer.title, description=layer.description, auth=settings.LAYMAN_GS_AUTH)
        if layer.style_type == 'qml':
            gs_util.patch_wms_layer(gs_layer_ids.workspace, gs_layer_ids.name, title=layer.title, description=layer.description, auth=settings.LAYMAN_GS_AUTH)
    elif geodata_type == settings.GEODATA_TYPE_RASTER:
        image_mosaic = layer.image_mosaic
        if image_mosaic:
            store = get_image_mosaic_store_name(uuid=layer.uuid)
        else:
            store = get_geotiff_store_name(uuid=layer.uuid)
        gs_util.patch_coverage(gs_layer_ids.workspace, gs_layer_ids.name, store, title=layer.title, description=layer.description, auth=settings.LAYMAN_GS_AUTH)
    else:
        raise NotImplementedError(f"Unknown geodata type: {geodata_type}")
    clear_cache()

    if layer.access_rights and layer.access_rights.get('read'):
        security_read_roles = gs_common.layman_users_and_roles_to_geoserver_roles(layer.access_rights['read'])
        gs_util.ensure_layer_security_roles(gs_layer_ids.workspace, gs_layer_ids.name, security_read_roles, 'r', settings.LAYMAN_GS_AUTH)

    if layer.access_rights and layer.access_rights.get('write'):
        security_write_roles = gs_common.layman_users_and_roles_to_geoserver_roles(layer.access_rights['write'])
        gs_util.ensure_layer_security_roles(gs_layer_ids.workspace, gs_layer_ids.name, security_write_roles, 'w', settings.LAYMAN_GS_AUTH)


def delete_layer(layer: Layer):
    db_store_name = DEFAULT_INTERNAL_DB_STORE
    gs_layername = layer.gs_ids.wms
    gs_util.delete_feature_type(gs_layername.workspace, gs_layername.name, settings.LAYMAN_GS_AUTH, store=db_store_name)
    gs_util.delete_feature_type(gs_layername.workspace, gs_layername.name, settings.LAYMAN_GS_AUTH, store=get_external_db_store_name(uuid=layer.uuid))
    gs_util.delete_wms_layer(gs_layername.workspace, gs_layername.name, settings.LAYMAN_GS_AUTH)
    gs_util.delete_wms_store(gs_layername.workspace, settings.LAYMAN_GS_AUTH, get_qgis_store_name(uuid=layer.uuid))
    gs_util.delete_coverage_store(gs_layername.workspace, settings.LAYMAN_GS_AUTH, get_geotiff_store_name(uuid=layer.uuid))
    gs_util.delete_coverage_store(gs_layername.workspace, settings.LAYMAN_GS_AUTH, get_image_mosaic_store_name(uuid=layer.uuid))
    gs_util.delete_db_store(gs_layername.workspace, settings.LAYMAN_GS_AUTH, store_name=get_external_db_store_name(uuid=layer.uuid))
    clear_cache()

    gs_util.delete_security_roles(f"{gs_layername.workspace}.{gs_layername.name}.r", settings.LAYMAN_GS_AUTH)
    gs_util.delete_security_roles(f"{gs_layername.workspace}.{gs_layername.name}.w", settings.LAYMAN_GS_AUTH)
    return {}


def get_wms_url(external_url=False, *, x_forwarded_items=None):
    workspace = layman.layer.geoserver.GEOSERVER_WMS_WORKSPACE
    assert external_url or not x_forwarded_items
    base_url = get_gs_proxy_server_url(x_forwarded_items=x_forwarded_items) + settings.LAYMAN_GS_PATH \
        if external_url else settings.LAYMAN_GS_URL
    return urljoin(base_url, workspace + '/ows')


def get_wms_direct():
    headers = {
        settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE: settings.LAYMAN_GS_USER,
    }
    ows_url = get_wms_url()
    from geoserver.util import wms_direct
    key = get_flask_proxy_key()
    redis_obj = settings.LAYMAN_REDIS.hgetall(key)
    string_value = redis_obj['value'] if redis_obj else None
    return wms_direct(ows_url, xml=string_value, headers=headers)


def get_wms_proxy():
    headers = {
        settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE: settings.LAYMAN_GS_USER,
        'X-Forwarded-Path': '',
        'X-Forwarded-Proto': settings.LAYMAN_PUBLIC_URL_SCHEME,
        'X-Forwarded-Host': settings.LAYMAN_PROXY_SERVER_NAME,
    }
    key = get_flask_proxy_key()

    ows_url = get_wms_url()

    def create_string_value():
        response = requests_util.retry.get_session().get(ows_url, params={
            'SERVICE': 'WMS',
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
        from .util import wms_proxy
        wms_proxy = wms_proxy(ows_url, xml=string_value, headers=headers)
        return wms_proxy

    def currently_changing():
        layerinfos = layman_util.get_publication_infos(publ_type=LAYER_TYPE)
        result = any((
            not is_layer_chain_ready(workspace, layername)
            for (workspace, _, layername) in layerinfos
        ))
        return result

    wms_proxy = mem_redis.get(key, create_string_value, mem_value_from_string_value, currently_changing)
    return wms_proxy


def clear_cache():
    key = get_flask_proxy_key()
    mem_redis.delete(key)


def get_timeregex_props(layer_dir):
    props_path = os.path.join(layer_dir, 'timeregex.properties')
    props_config = configparser.ConfigParser()
    section_name = 'global'
    try:
        with open(props_path, encoding="utf-8") as props_file:
            props_config.read_file(itertools.chain([f'[{section_name}]'], props_file), source=props_path)
            regex = props_config[section_name]['regex']
        split = regex.split(',format=')
        result = {
            'regex': split[0],
        }
        if len(split) > 1:
            result['regex_format'] = split[1]
    except IOError:
        result = {}
        logger.warning(f"File {props_path} seems not to exist or not to be readable.")
    return result


def get_layer_info(workspace, layername, *, x_forwarded_items=None):
    uuid = layman_util.get_publication_uuid(workspace, LAYER_TYPE, layername)
    return get_layer_info_by_uuid(uuid=uuid, x_forwarded_items=x_forwarded_items)


def get_layer_info_by_uuid(*, uuid, x_forwarded_items=None):
    gs_layername = GeoserverIds(uuid=uuid, ).wms
    if uuid is None:
        return {}
    time_info = None
    wms_layer = gs_util.get_layer(gs_layername.workspace, gs_layername.name, auth=settings.LAYMAN_GS_AUTH)
    if not wms_layer:
        return {}
    if wms_layer['resource']['@class'] == 'coverage' \
            and get_image_mosaic_store_name(uuid=uuid) in wms_layer['resource']['href']:
        granules_json = gs_util.get_image_mosaic_granules(gs_layername.workspace,
                                                          get_image_mosaic_store_name(uuid=uuid),
                                                          gs_layername.name)
        if granules_json:
            gdal_layer_dir = gdal.get_normalized_raster_layer_dir(uuid)
            time_info = {
                **image_mosaic_granules_to_wms_time_key(granules_json),
                **get_timeregex_props(gdal_layer_dir),
            }

    wms_proxy_url = get_wms_url(external_url=True, x_forwarded_items=x_forwarded_items)

    result = {
        'wms': {
            'name': gs_layername.name,
            'url': wms_proxy_url,
        },
        '_wms': {
            'url': get_wms_url(external_url=False),
            'workspace': gs_layername.workspace,
        },
    }
    if time_info:
        result['wms']['time'] = time_info
    return result


def get_metadata_comparison(layer: Layer):
    gs_layername = layer.gs_ids.wms
    wms = get_wms_direct()
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
    wms_layer = wms.contents.get(gs_layername.name, None)
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
    except BaseException as exc:
        current_app.logger.error(exc)
        reference_system = None

    temporal_extent = wms.contents[gs_layername.name].dimensions['time']['values'] if gs_layername.name in wms.contents and 'time' in wms.contents[gs_layername.name].dimensions else None

    props = {
        'wms_url': wms_url,
        'title': title,
        'abstract': abstract,
        'extent': extent,
        'reference_system': reference_system,
        'temporal_extent': temporal_extent,
    }
    # current_app.logger.info(f"props:\n{json.dumps(props, indent=2)}")
    url = get_capabilities_url()
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
    url_parsed = urlparse(url)
    query = parse_qs(url_parsed.query, keep_blank_values=True)
    for param_key in list(query.keys()):
        if param_key.lower() in params:
            query.pop(param_key, None)
    url_parsed = url_parsed._replace(query=urlencode(query, True))
    url = urlunparse(url_parsed)
    return url


def add_capabilities_params_to_url(url):
    params = {'SERVICE': 'WMS', 'REQUEST': 'GetCapabilities', 'VERSION': VERSION}
    url = add_params_to_url(url, params)
    return url


def get_capabilities_url():
    url = get_wms_url(external_url=True)
    url = add_capabilities_params_to_url(url)
    return url


def get_layman_workspace(geoserver_workspace):
    workspace = geoserver_workspace[:-len(settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX)] if geoserver_workspace.endswith(
        settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX) else geoserver_workspace
    return workspace


def get_qgis_store_name(*, uuid):
    return f'{DEFAULT_WMS_QGIS_STORE_PREFIX}_{uuid}'


def get_geotiff_store_name(*, uuid):
    return f'{DEFAULT_GEOTIFF_STORE_PREFIX}_{uuid}'


def get_image_mosaic_store_name(*, uuid):
    return f'{DEFAULT_IMAGE_MOSAIC_STORE_PREFIX}_{uuid}'
