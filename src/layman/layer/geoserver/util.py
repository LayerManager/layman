import logging
from urllib.parse import urlparse

import crs as crs_def
from geoserver import util as gs_util
from layman import settings, util as layman_util
from layman.common import bbox as bbox_util, geoserver as gs_common
from layman.layer.geoserver import wms
from layman.layer.layer_class import Layer
from layman.util import XForwardedClass

logger = logging.getLogger(__name__)
CACHE_GS_PROXY_BASE_URL_KEY = f'{__name__}:GS_PROXY_BASE_URL'
DEFAULT_EXTERNAL_DB_STORE_PREFIX = 'external_db'
DEFAULT_INTERNAL_DB_STORE = 'postgresql'


def get_gs_proxy_server_url(*, x_forwarded_items=None):
    x_forwarded_items = x_forwarded_items or XForwardedClass()
    protocol = x_forwarded_items.proto or settings.LAYMAN_PUBLIC_URL_SCHEME
    host = x_forwarded_items.host or settings.LAYMAN_PROXY_SERVER_NAME
    path_prefix = x_forwarded_items.prefix or ''
    proxy_base_url = f'{protocol}://{host}{path_prefix}'
    return proxy_base_url


def wms_proxy(wms_url, xml=None, version=None, headers=None):
    from layman.layer.geoserver.wms import VERSION
    version = version or VERSION
    wms_url_path = urlparse(wms_url).path
    # current_app.logger.info(f"xml=\n{xml}")
    wms = gs_util.wms_direct(wms_url, xml=xml, version=version, headers=headers)
    if wms:
        for operation in wms.operations:
            # app.logger.info(operation.name)
            for method in operation.methods:
                method_url = urlparse(method['url'])
                method_url = method_url._replace(
                    netloc=settings.LAYMAN_GS_HOST + ':' + settings.LAYMAN_GS_PORT,
                    path=wms_url_path,
                    scheme='http'
                )
                method['url'] = method_url.geturl()
    return wms


def wfs_proxy(wfs_url, xml=None, version=None, headers=None):
    from layman.layer.geoserver.wfs import VERSION
    version = version or VERSION
    wfs_url_path = urlparse(wfs_url).path
    wfs = gs_util.wfs_direct(wfs_url, xml=xml, version=version, headers=headers)
    for operation in wfs.operations:
        # app.logger.info(operation.name)
        for method in operation.methods:
            method_url = urlparse(method['url'])
            method_url = method_url._replace(
                netloc=settings.LAYMAN_GS_HOST + ':' + settings.LAYMAN_GS_PORT,
                path=wfs_url_path,
                scheme='http'
            )
            method['url'] = method_url.geturl()
    return wfs


def get_external_db_store_name(*, uuid):
    return f'{DEFAULT_EXTERNAL_DB_STORE_PREFIX}_{uuid}'


def get_db_store_name(*, uuid, original_data_source):
    return get_external_db_store_name(uuid=uuid) if original_data_source == settings.EnumOriginalDataSource.TABLE.value \
        else DEFAULT_INTERNAL_DB_STORE


def image_mosaic_granules_to_wms_time_key(granules_json):
    values = sorted(set(feature['properties']['ingestion'] for feature in granules_json['features']))
    return {
        'units': 'ISO8601',
        'values': values,
        'default': max(values),
    }


def publish_layer_from_qgis(*, layer: Layer, gs_names, metadata_url, ):
    store_name = wms.get_qgis_store_name(uuid=layer.uuid)
    info = layman_util.get_publication_info_by_class(layer, context={'keys': ['wms', ]})
    layer_capabilities_url = info['_wms']['qgis_capabilities_url']
    gs_util.create_wms_store(gs_names.workspace,
                             settings.LAYMAN_GS_AUTH,
                             store_name,
                             layer_capabilities_url)
    bbox = get_layer_bbox(layer=layer)
    lat_lon_bbox = bbox_util.transform(bbox, layer.native_crs, crs_def.EPSG_4326)
    gs_util.post_wms_layer(gs_names.workspace, gs_names.name, layer.qgis_names.name, store_name, layer.title, layer.description, bbox, layer.native_crs, settings.LAYMAN_GS_AUTH,
                           lat_lon_bbox=lat_lon_bbox, metadata_url=metadata_url)


def create_external_db_store(workspace, *, uuid, table_uri, auth=settings.LAYMAN_GS_AUTH):
    pg_conn = {
        'host': table_uri.hostname,
        'port': table_uri.port,
        'dbname': table_uri.db_name,
        'user': table_uri.username,
        'password': table_uri.password,
    }
    store_name = get_external_db_store_name(uuid=uuid)
    gs_util.create_db_store(workspace,
                            auth,
                            db_schema=table_uri.schema,
                            pg_conn=pg_conn,
                            name=store_name,
                            )
    return store_name


def set_security_rules(*, layer: Layer, gs_names, access_rights, auth, ):
    read_roles = access_rights.get('read') if access_rights and access_rights.get('read') else layer.access_rights['read']
    write_roles = access_rights.get('write') if access_rights and access_rights.get('write') else layer.access_rights['write']

    security_read_roles = gs_common.layman_users_and_roles_to_geoserver_roles(read_roles)
    gs_util.ensure_layer_security_roles(gs_names.workspace, gs_names.name, security_read_roles, 'r', auth)

    security_write_roles = gs_common.layman_users_and_roles_to_geoserver_roles(write_roles)
    gs_util.ensure_layer_security_roles(gs_names.workspace, gs_names.name, security_write_roles, 'w', auth)


def get_layer_bbox(*, layer: Layer):
    # GeoServer is not working good with degradeted bbox
    result = bbox_util.get_bbox_to_publish(layer.native_bounding_box, layer.native_crs)
    return result


def publish_layer_from_db(*, layer: Layer, gs_names, metadata_url, store_name=None):
    bbox = get_layer_bbox(layer=layer)
    lat_lon_bbox = bbox_util.transform(bbox, layer.native_crs, crs_def.EPSG_4326)
    gs_util.post_feature_type(gs_names.workspace, gs_names.name, layer.description, layer.title, bbox, layer.native_crs, settings.LAYMAN_GS_AUTH, lat_lon_bbox=lat_lon_bbox, table_name=layer.table_uri.table, metadata_url=metadata_url, store_name=store_name)
