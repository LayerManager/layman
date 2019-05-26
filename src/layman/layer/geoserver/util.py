import requests
from urllib.parse import urljoin, urlparse
from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService

from werkzeug.contrib.cache import SimpleCache
cache = SimpleCache()

headers_json = {
    'Accept': 'application/json',
    'Content-type': 'application/json',
}

CACHE_GS_PROXY_BASE_URL_KEY = f'{__name__}:GS_PROXY_BASE_URL:'

from layman import settings


def get_gs_proxy_base_url():
    proxy_base_url = cache.get(CACHE_GS_PROXY_BASE_URL_KEY)
    if proxy_base_url is None:
        try:
            r = requests.get(
                settings.LAYMAN_GS_REST_SETTINGS,
                headers={
                    'Accept': 'application/json',
                    'Content-type': 'application/json',
                },
                auth=settings.LAYMAN_GS_AUTH
            )
            if r.status_code == 200:
                proxy_base_url = r.json()['global']['settings'].get(
                    'proxyBaseUrl', None)
        except:
            pass
        if proxy_base_url is not None:
            cache.set(CACHE_GS_PROXY_BASE_URL_KEY, proxy_base_url, timeout=1 * 60)
    return proxy_base_url


def get_feature_type(
        workspace, data_store, feature_type,
        gs_rest_workspaces=settings.LAYMAN_GS_REST_WORKSPACES):
    r_url = urljoin(gs_rest_workspaces,
                    f'{workspace}/datastores/{data_store}/featuretypes/{feature_type}')
    r = requests.get(r_url,
        headers=headers_json,
        auth=settings.LAYMAN_GS_AUTH
    )
    r.raise_for_status()
    return r.json()['featureType']

def wms_proxy(wms_url):
    wms_url_path = urlparse(wms_url).path
    wms = WebMapService(wms_url)
    for operation in wms.operations:
        # app.logger.info(operation.name)
        for method in operation.methods:
            method_url = urlparse(method['url'])
            method_url = method_url._replace(
                netloc = settings.LAYMAN_GS_HOST + ':' + settings.LAYMAN_GS_PORT,
                path = wms_url_path)
            method['url'] = method_url.geturl()
    return wms

def wfs_proxy(wfs_url):
    wfs_url_path = urlparse(wfs_url).path
    wfs = WebFeatureService(wfs_url)
    for operation in wfs.operations:
        # app.logger.info(operation.name)
        for method in operation.methods:
            method_url = urlparse(method['url'])
            method_url = method_url._replace(
                netloc = settings.LAYMAN_GS_HOST + ':' + settings.LAYMAN_GS_PORT,
                path = wfs_url_path)
            method['url'] = method_url.geturl()
    return wfs
