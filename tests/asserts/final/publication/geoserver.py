import requests

from layman import app, settings, util as layman_util
from test_tools import util as test_util


def workspace_wms_1_3_0_capabilities_available(workspace):
    with app.app_context():
        internal_wms_url = test_util.url_for('geoserver_proxy_bp.proxy', subpath=workspace + settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX + '/ows')

    r_wms = requests.get(internal_wms_url, params={
        'service': 'WMS',
        'request': 'GetCapabilities',
        'version': '1.3.0',
    })
    assert r_wms.status_code == 200


def workspace_wfs_2_0_0_capabilities_available_if_vector(workspace, publ_type, name):
    with app.app_context():
        internal_wfs_url = test_util.url_for('geoserver_proxy_bp.proxy', subpath=workspace + '/wfs')

    with app.app_context():
        file_info = layman_util.get_publication_info(workspace, publ_type, name, {'keys': ['file']})['file']
    file_type = file_info['file_type']
    if file_type == settings.FILE_TYPE_VECTOR:
        r_wfs = requests.get(internal_wfs_url, params={
            'service': 'WFS',
            'request': 'GetCapabilities',
            'version': '2.0.0',
        })
        assert r_wfs.status_code == 200
