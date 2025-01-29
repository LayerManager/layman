import configparser
from urllib.parse import urljoin
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs, parse_qsl
import itertools
import logging
import os
from flask import current_app

from geoserver import util as gs_util
from layman import settings, patch_mode, util as layman_util, names
from layman.cache import mem_redis
from layman.common import geoserver as gs_common, empty_method_returns_none, empty_method
from layman.layer.util import is_layer_chain_ready
from layman.layer import LAYER_TYPE
from layman.layer.filesystem import gdal
import requests_util.retry
from .util import get_gs_proxy_server_url, get_external_db_store_name

FLASK_PROXY_KEY = f'{__name__}:PROXY:{{workspace}}'
DEFAULT_WMS_QGIS_STORE_PREFIX = 'qgis'
DEFAULT_GEOTIFF_STORE_PREFIX = 'geotiff'
DEFAULT_IMAGE_MOSAIC_STORE_PREFIX = 'image_mosaic'

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT
VERSION = gs_util.WMS_VERSION
logger = logging.getLogger(__name__)

pre_publication_action_check = empty_method
post_layer = empty_method
get_publication_uuid = empty_method_returns_none


def get_flask_proxy_key(workspace):
    return FLASK_PROXY_KEY.format(workspace=workspace)


def patch_layer_by_uuid(*, uuid, gdal_layername, gdal_workspace, original_data_source, title, description, access_rights=None):
    gs_layername = names.get_layer_names_by_source(uuid=uuid, ).wms
    if not get_layer_info_by_uuid(uuid=uuid, gdal_layername=gdal_layername, gdal_workspace=gdal_workspace,):
        return
    info = layman_util.get_publication_info_by_uuid(uuid, context={'keys': ['style_type', 'geodata_type', 'image_mosaic'], })
    geodata_type = info['geodata_type']
    if geodata_type == settings.GEODATA_TYPE_VECTOR:
        if info['_style_type'] == 'sld':
            store_name = get_external_db_store_name(uuid=uuid) if original_data_source == settings.EnumOriginalDataSource.TABLE.value else gs_util.DEFAULT_DB_STORE_NAME
            gs_util.patch_feature_type(gs_layername.workspace, gs_layername.name, store_name=store_name, title=title, description=description, auth=settings.LAYMAN_GS_AUTH)
        if info['_style_type'] == 'qml':
            gs_util.patch_wms_layer(gs_layername.workspace, gs_layername.name, title=title, description=description, auth=settings.LAYMAN_GS_AUTH)
    elif geodata_type == settings.GEODATA_TYPE_RASTER:
        image_mosaic = info['image_mosaic']
        if image_mosaic:
            store = get_image_mosaic_store_name(uuid=uuid)
        else:
            store = get_geotiff_store_name(uuid=uuid)
        gs_util.patch_coverage(gs_layername.workspace, gs_layername.name, store, title=title, description=description, auth=settings.LAYMAN_GS_AUTH)
    else:
        raise NotImplementedError(f"Unknown geodata type: {geodata_type}")
    clear_cache(gs_layername.workspace)

    if access_rights and access_rights.get('read'):
        security_read_roles = gs_common.layman_users_and_roles_to_geoserver_roles(access_rights['read'])
        gs_util.ensure_layer_security_roles(gs_layername.workspace, gs_layername.name, security_read_roles, 'r', settings.LAYMAN_GS_AUTH)

    if access_rights and access_rights.get('write'):
        security_write_roles = gs_common.layman_users_and_roles_to_geoserver_roles(access_rights['write'])
        gs_util.ensure_layer_security_roles(gs_layername.workspace, gs_layername.name, security_write_roles, 'w', settings.LAYMAN_GS_AUTH)


# pylint: disable=unused-argument
def patch_layer(workspace, layername, *, uuid, title, description, original_data_source, access_rights=None):
    patch_layer_by_uuid(uuid=uuid,
                        gdal_layername=layername,
                        gdal_workspace=workspace,
                        title=title,
                        description=description,
                        original_data_source=original_data_source,
                        access_rights=access_rights,
                        )


def delete_layer_by_uuid(*, uuid):
    gs_layername = names.get_names_by_source(uuid=uuid, publication_type=LAYER_TYPE).wms
    gs_util.delete_feature_type(gs_layername.workspace, gs_layername.name, settings.LAYMAN_GS_AUTH)
    gs_util.delete_feature_type(gs_layername.workspace, gs_layername.name, settings.LAYMAN_GS_AUTH, store=get_external_db_store_name(uuid=uuid))
    gs_util.delete_wms_layer(gs_layername.workspace, gs_layername.name, settings.LAYMAN_GS_AUTH)
    gs_util.delete_wms_store(gs_layername.workspace, settings.LAYMAN_GS_AUTH, get_qgis_store_name(uuid=uuid))
    gs_util.delete_coverage_store(gs_layername.workspace, settings.LAYMAN_GS_AUTH, get_geotiff_store_name(uuid=uuid))
    gs_util.delete_coverage_store(gs_layername.workspace, settings.LAYMAN_GS_AUTH, get_image_mosaic_store_name(uuid=uuid))
    gs_util.delete_db_store(gs_layername.workspace, settings.LAYMAN_GS_AUTH, store_name=get_external_db_store_name(uuid=uuid))
    clear_cache(gs_layername.workspace)

    gs_util.delete_security_roles(f"{gs_layername.workspace}.{gs_layername.name}.r", settings.LAYMAN_GS_AUTH)
    gs_util.delete_security_roles(f"{gs_layername.workspace}.{gs_layername.name}.w", settings.LAYMAN_GS_AUTH)
    return {}


def delete_layer(workspace, layername):
    uuid = layman_util.get_publication_uuid(workspace, LAYER_TYPE, layername)
    return delete_layer_by_uuid(uuid=uuid, )


def get_wms_url(workspace, external_url=False, *, x_forwarded_items=None):
    assert external_url or not x_forwarded_items
    base_url = get_gs_proxy_server_url(x_forwarded_items=x_forwarded_items) + settings.LAYMAN_GS_PATH \
        if external_url else settings.LAYMAN_GS_URL
    return urljoin(base_url, workspace + '/ows')


def get_wms_direct(workspace):
    headers = {
        settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE: settings.LAYMAN_GS_USER,
    }
    ows_url = get_wms_url(workspace)
    from .util import wms_direct
    key = get_flask_proxy_key(workspace)
    redis_obj = settings.LAYMAN_REDIS.hgetall(key)
    string_value = redis_obj['value'] if redis_obj else None
    return wms_direct(ows_url, xml=string_value, headers=headers)


def get_wms_proxy(workspace):
    headers = {
        settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE: settings.LAYMAN_GS_USER,
        'X-Forwarded-Path': '',
        'X-Forwarded-Proto': settings.LAYMAN_PUBLIC_URL_SCHEME,
        'X-Forwarded-Host': settings.LAYMAN_PROXY_SERVER_NAME,
    }
    key = get_flask_proxy_key(workspace)

    ows_url = get_wms_url(workspace)

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
        layerinfos = layman_util.get_publication_infos(workspace, LAYER_TYPE)
        result = any((
            not is_layer_chain_ready(workspace, layername)
            for (_, _, layername) in layerinfos
        ))
        return result

    wms_proxy = mem_redis.get(key, create_string_value, mem_value_from_string_value, currently_changing)
    return wms_proxy


def clear_cache(workspace):
    key = get_flask_proxy_key(workspace)
    mem_redis.delete(key)


def get_timeregex_props(workspace, layername):
    layer_dir = gdal.get_normalized_raster_layer_dir(workspace, layername)
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
    return get_layer_info_by_uuid(uuid=uuid, gdal_layername=layername, gdal_workspace=workspace, x_forwarded_items=x_forwarded_items)


def get_layer_info_by_uuid(*, uuid, gdal_layername, gdal_workspace, x_forwarded_items=None):
    gs_layername = names.get_layer_names_by_source(uuid=uuid, ).wms
    wms = get_wms_proxy(gs_layername.workspace)
    if wms is None or uuid is None:
        return {}
    wms_proxy_url = get_wms_url(gs_layername.workspace, external_url=True, x_forwarded_items=x_forwarded_items)

    if gs_layername.name not in wms.contents:
        return {}
    result = {
        'title': wms.contents[gs_layername.name].title,
        'description': wms.contents[gs_layername.name].abstract,
        'wms': {
            'name': gs_layername.name,
            'url': wms_proxy_url,
        },
        '_wms': {
            'url': get_wms_url(gs_layername.workspace, external_url=False),
            'workspace': gs_layername.workspace,
        },
    }
    if 'time' in wms.contents[gs_layername.name].dimensions:
        result['wms']['time'] = {
            **wms.contents[gs_layername.name].dimensions['time'],
            **get_timeregex_props(gdal_workspace, gdal_layername),
        }
    return result


def get_metadata_comparison(workspace, layername):
    uuid = layman_util.get_publication_uuid(workspace, LAYER_TYPE, layername)
    return get_metadata_comparison_by_uuid(uuid=uuid)


def get_metadata_comparison_by_uuid(*, uuid):
    gs_layername = names.get_layer_names_by_source(uuid=uuid, ).wms
    wms = get_wms_direct(gs_layername.workspace)
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
    url = get_capabilities_url(gs_layername.workspace)
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


def get_capabilities_url(workspace):
    url = get_wms_url(workspace, external_url=True)
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
