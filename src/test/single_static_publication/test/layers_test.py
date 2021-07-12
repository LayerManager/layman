import requests
import pytest

from layman import settings, app
from test_tools import process_client
from test_tools.util import url_for
from ... import single_static_publication as data
from ..data import ensure_publication


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_LAYERS)
@pytest.mark.usefixtures('ensure_layman')
def test_info(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    wms_url = f"http://localhost:8000/geoserver/{workspace}{settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX}/ows"
    wfs_url = f"http://localhost:8000/geoserver/{workspace}/wfs"

    info = process_client.get_workspace_publication(publ_type, workspace, publication)

    assert info['wms'].get('url') == wms_url, f'r_json={info}, wms_url={wms_url}'
    assert 'wms' in info, f'info={info}'
    assert 'url' in info['wms'], f'info={info}'

    if data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('file_type') == 'vector':
        assert info.get('file', dict()).get('file_type') == 'vector', info
        assert 'wfs' in info, f'info={info}'
        assert 'url' in info['wms'], f'info={info}'
        assert info['wfs'].get('url') == wfs_url, f'r_json={info}, wfs_url={wfs_url}'
    elif data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('file_type') == 'raster':
        assert info.get('file', dict()).get('file_type') == 'raster', info
        assert 'wfs' not in info, f'info={info}'
        assert 'db_table' not in info, f'info={info}'


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_VECTOR_LAYERS)
@pytest.mark.usefixtures('ensure_layman')
def test_wms_workspace(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

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
