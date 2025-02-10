import logging
from urllib.parse import urlparse
from layman import settings
from layman.util import XForwardedClass
from geoserver.util import wms_direct, wfs_direct

logger = logging.getLogger(__name__)
CACHE_GS_PROXY_BASE_URL_KEY = f'{__name__}:GS_PROXY_BASE_URL'
DEFAULT_EXTERNAL_DB_STORE_PREFIX = 'external_db'
DEFAULT_INTERNAL_DB_STORE_PREFIX = 'postgresql'


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
    wms = wms_direct(wms_url, xml=xml, version=version, headers=headers)
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
    wfs = wfs_direct(wfs_url, xml=xml, version=version, headers=headers)
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


def get_internal_db_store_name(*, db_schema):
    return f'{DEFAULT_INTERNAL_DB_STORE_PREFIX}_{db_schema}'


def get_db_store_name(*, uuid, db_schema, original_data_source):
    return get_external_db_store_name(uuid=uuid) if original_data_source == settings.EnumOriginalDataSource.TABLE.value \
        else get_internal_db_store_name(db_schema=db_schema)


def image_mosaic_granules_to_wms_time_key(granules_json):
    values = sorted(set(feature['properties']['ingestion'] for feature in granules_json['features']))
    return {
        'units': 'ISO8601',
        'values': values,
        'default': max(values),
    }
