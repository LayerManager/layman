import requests

headers_json = {
    'Accept': 'application/json',
    'Content-type': 'application/json',
}

GS_PROXY_BASE_URL = None

from .settings import LAYMAN_GS_REST_SETTINGS, LAYMAN_GS_AUTH
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


