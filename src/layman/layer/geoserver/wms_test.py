import pytest
from test import process_client
from layman import settings, app
from layman.util import url_for
import requests


@pytest.mark.usefixtures('ensure_layman_module')
def test_wms_workspace():
    workspace = 'test_wms_workspace_workspace'
    layername = 'test_wms_workspace_layer'

    wms_url = f"http://localhost:8000/geoserver/test_wms_workspace_workspace{settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX}/ows"
    wfs_url = f"http://localhost:8000/geoserver/test_wms_workspace_workspace/wfs"

    process_client.publish_workspace_layer(workspace, layername)
    r_json = process_client.get_workspace_layer(workspace, layername)
    assert r_json['wms']['url'] == wms_url
    assert r_json['wfs']['url'] == wfs_url

    with app.app_context():
        internal_wms_url = url_for('geoserver_proxy_bp.proxy', subpath=workspace + settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX + '/ows')
        internal_wfs_url = url_for('geoserver_proxy_bp.proxy', subpath=workspace + '/wfs')

    r_wms = requests.get(internal_wms_url, params={
        'service': 'WMS',
        'request': 'GetCapabilities',
        'version': '1.3.0',
    })
    assert r_wms.status_code == 200

    r_wfs = requests.get(internal_wfs_url, params={
        'service': 'WFS',
        'request': 'GetCapabilities',
        'version': '2.0.0',
    })
    assert r_wfs.status_code == 200

    process_client.delete_workspace_layer(workspace, layername)
