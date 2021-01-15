import requests
from layman import app
from layman.util import url_for
from layman.layer.geoserver.util import wfs_direct, wms_direct
from layman.layer.geoserver import wfs


def get_url(workspace, service_endpoint):
    with app.app_context():
        wfs_url = url_for('gs_wfs_proxy_bp.proxy', subpath=workspace + '/' + service_endpoint)
    return wfs_url


def get_wms_url(workspace, service_endpoint='ows'):
    return get_url(workspace, service_endpoint)


def get_wfs_url(workspace, service_endpoint='wfs'):
    return get_url(workspace, service_endpoint)


def get_wfs_capabilities(workspace=None, service_endpoint='wfs', headers=None):
    wfs_url = get_url(workspace, service_endpoint)
    return wfs_direct(wfs_url, headers=headers)


def get_wms_capabilities(workspace=None, service_endpoint='ows', headers=None):
    wms_url = get_url(workspace, service_endpoint)
    return wms_direct(wms_url, headers=headers)


def get_features(workspace, feature_type, epsg_code=3857):
    wfs_url = get_wfs_url(workspace)
    epsg_name = f"urn:ogc:def:crs:EPSG::{epsg_code}"
    r = requests.get(wfs_url, params={
        'service': 'WFS',
        'request': 'GetFeature',
        'version': wfs.VERSION,
        'typeNames': f"{workspace}:{feature_type}",
        'outputFormat': f"application/json",
        'srsName': epsg_name,
    })
    r.raise_for_status()
    result = r.json()
    assert result['crs']['properties']['name'] == epsg_name
    return result
