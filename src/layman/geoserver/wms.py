from urllib.parse import urljoin

from flask import g, current_app

from layman.settings import *

def get_wms_proxy(username):
    key = 'layman.geoserver.wms_proxy'
    if key not in g:
        wms_url = urljoin(LAYMAN_GS_URL, username + '/ows')
        from .util import wms_proxy
        wms_proxy = wms_proxy(wms_url)
        g.setdefault(key, wms_proxy)
    return g.get(key)

def get_layer_info(username, layername):

    try:
        wms = get_wms_proxy(username)
        wms_proxy_url = urljoin(LAYMAN_GS_PROXY_URL, username + '/ows')

        return {
            'title': wms.contents[layername].title,
            'description': wms.contents[layername].abstract,
            'wms': {
                'url': wms_proxy_url
            },
        }
    except:
        return {}


def get_layer_names(username):
    try:
        wms = get_wms_proxy(username)

        return [*wms.contents]
    except:
        return []