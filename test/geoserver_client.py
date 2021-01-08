from layman import app
from layman.util import url_for
from layman.layer.geoserver.util import wfs_direct, wms_direct


def get_url(workspace, service_endpoint):
    with app.app_context():
        wfs_url = url_for('gs_wfs_proxy_bp.proxy', subpath=workspace + '/' + service_endpoint)
    return wfs_url


def get_wms_url(workspace, service_endpoint='ows'):
    return get_url(workspace, service_endpoint)


def get_wfs_capabilities(workspace=None, service_endpoint='wfs', headers=None):
    wfs_url = get_url(workspace, service_endpoint)
    return wfs_direct(wfs_url, headers=headers)


def get_wms_capabilities(workspace=None, service_endpoint='ows', headers=None):
    wms_url = get_url(workspace, service_endpoint)
    return wms_direct(wms_url, headers=headers)
