import requests
from urllib.parse import urljoin, urlparse
from owslib.wms import WebMapService

headers_json = {
    'Accept': 'application/json',
    'Content-type': 'application/json',
}

GS_PROXY_BASE_URL = None

from .settings import LAYMAN_GS_REST_SETTINGS, LAYMAN_GS_AUTH, \
    LAYMAN_GS_REST_WORKSPACES, LAYMAN_GS_HOST, LAYMAN_GS_PORT, LAYMAN_GS_PATH
def get_gs_proxy_base_url():
    global GS_PROXY_BASE_URL
    if GS_PROXY_BASE_URL is None:
        try:
            r = requests.get(
                LAYMAN_GS_REST_SETTINGS,
                headers={
                    'Accept': 'application/json',
                    'Content-type': 'application/json',
                },
                auth=LAYMAN_GS_AUTH
            )
            if r.status_code == 200:
                GS_PROXY_BASE_URL = r.json()['global']['settings'].get('proxyBaseUrl', None)
        except:
            pass
    return GS_PROXY_BASE_URL


def get_feature_type(
        workspace, data_store, feature_type,
        gs_rest_workspaces=LAYMAN_GS_REST_WORKSPACES):
    r_url = urljoin(gs_rest_workspaces,
                    '{}/datastores/{}/featuretypes/{}'.format(workspace,
                                                              data_store,
                                                              feature_type))
    r = requests.get(r_url,
        headers=headers_json,
        auth=LAYMAN_GS_AUTH
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
                netloc = LAYMAN_GS_HOST + ':' + LAYMAN_GS_PORT,
                path = wms_url_path)
            method['url'] = method_url.geturl()
    return wms
