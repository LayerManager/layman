import logging
from urllib.parse import urlparse
import requests.exceptions
from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService

from geoserver.util import get_proxy_base_url
from layman.cache.mem import CACHE as MEM_CACHE


logger = logging.getLogger(__name__)
CACHE_GS_PROXY_BASE_URL_KEY = f'{__name__}:GS_PROXY_BASE_URL'

from layman import settings


def get_gs_proxy_base_url():
    proxy_base_url = MEM_CACHE.get(CACHE_GS_PROXY_BASE_URL_KEY)
    if proxy_base_url is None:
        proxy_base_url = get_proxy_base_url(settings.LAYMAN_GS_AUTH)
        MEM_CACHE.set(CACHE_GS_PROXY_BASE_URL_KEY, proxy_base_url, ttl=settings.LAYMAN_CACHE_GS_TIMEOUT)
    return proxy_base_url


def wms_direct(wms_url, xml=None, version=None, headers=None):
    from layman.layer.geoserver.wms import VERSION
    version = version or VERSION
    try:
        wms = WebMapService(wms_url, xml=xml.encode('utf-8') if xml is not None else xml, version=version, headers=headers)
    except requests.exceptions.HTTPError as exc:
        if exc.response.status_code == 404:
            wms = None
        else:
            raise exc
    return wms


def wms_proxy(wms_url, xml=None, version=None, headers=None):
    from layman.layer.geoserver.wms import VERSION
    version = version or VERSION
    wms_url_path = urlparse(wms_url).path
    # current_app.logger.info(f"xml=\n{xml}")
    wms = wms_direct(wms_url, xml=xml, version=version, headers=headers)
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


def wfs_direct(wfs_url, xml=None, version=None, headers=None):
    from layman.layer.geoserver.wfs import VERSION
    version = version or VERSION
    try:
        wfs = WebFeatureService(wfs_url, xml=xml.encode('utf-8') if xml is not None else xml, version=version, headers=headers)
    except requests.exceptions.HTTPError as exc:
        if exc.response.status_code == 404:
            wfs = None
        else:
            raise exc
    return wfs


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
