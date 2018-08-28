from urllib.parse import urljoin

from flask import g, current_app

from layman.settings import *

def get_wfs_proxy(username):
    key = 'layman.geoserver.wfs_proxy'
    if key not in g:
        wms_url = urljoin(LAYMAN_GS_URL, username + '/ows')
        from .util import wms_proxy
        wms_proxy = wms_proxy(wms_url)
        g.setdefault(key, wms_proxy)
    return g.get(key)


def get_layer_info(username, layername):
    try:
        wfs = get_wfs_proxy(username)
        wfs_proxy_url = urljoin(LAYMAN_GS_PROXY_URL, username + '/ows')

        return {
            'title': wfs.contents[layername].title,
            'description': wfs.contents[layername].abstract,
            'wfs': {
                'url': wfs_proxy_url
            },
        }
    except:
        return {}


def get_layer_names(username):
    try:
        wfs = get_wfs_proxy(username)

        return [*wfs.contents]
    except:
        return []