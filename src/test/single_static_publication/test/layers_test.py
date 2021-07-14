import os
from urllib.parse import urljoin
import requests
from lxml import etree as ET
import pytest

from geoserver import GS_REST_WORKSPACES, GS_REST, GS_AUTH
from layman import settings, app
from layman.layer import util as layer_util
from layman.layer.geoserver.wms import DEFAULT_WMS_QGIS_STORE_PREFIX
from test_tools import process_client
from test_tools.util import url_for
from ... import single_static_publication as data
from ..data import ensure_publication


headers_sld = {
    'Accept': 'application/vnd.ogc.sld+xml',
    'Content-type': 'application/xml',
}


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_LAYERS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_info(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    wms_url = f"http://localhost:8000/geoserver/{workspace}{settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX}/ows"
    wfs_url = f"http://localhost:8000/geoserver/{workspace}/wfs"

    headers = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('headers')
    info = process_client.get_workspace_publication(publ_type, workspace, publication, headers=headers)

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


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_LAYERS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_geoserver_workspace(workspace, publ_type, publication):
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

    if data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('file_type') == 'vector':
        r_wfs = requests.get(internal_wfs_url, params={
            'service': 'WFS',
            'request': 'GetCapabilities',
            'version': '2.0.0',
        })
        assert r_wfs.status_code == 200


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_LAYERS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_get_layer_style(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    with app.app_context():
        headers = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('headers')
        rest_url = url_for('rest_workspace_layer_style.get', workspace=workspace, layername=publication)
    response = requests.get(rest_url, headers=headers)
    assert response.status_code == 200, response.text
    # lxml does not support importing from utf8 string
    xml_tree = ET.fromstring(bytes(response.text, encoding='utf8'))

    style_type = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA]['style_type']
    if style_type == 'sld':
        assert ET.QName(xml_tree) == "{http://www.opengis.net/sld}StyledLayerDescriptor", response.text
    elif style_type == 'qml':
        assert ET.QName(xml_tree), response.text
        assert ET.QName(xml_tree) == "qgis", response.text
        assert len(xml_tree.xpath('/qgis/renderer-v2')) == 1, response.text
        assert xml_tree.attrib, response.text


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_LAYERS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_wms_layer(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    style = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA]['style_type']
    style_file = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('style_file')
    expected_style_file = f'/layman_data_test/workspaces/{workspace}/layers/{publication}/input_style/{publication}'
    expected_qgis_file = f'/qgis/data/test/workspaces/{workspace}/layers/{publication}/{publication}.qgis'
    wms_stores_url = urljoin(GS_REST_WORKSPACES, f'{workspace}_wms/wmsstores/')
    wms_layers_url = urljoin(GS_REST_WORKSPACES, f'{workspace}_wms/wmslayers/')

    with app.app_context():
        info = layer_util.get_layer_info(workspace, publication, context={'keys': ['style_type', 'style'], })
    assert (info['style_type'] == 'qml') == (style == 'qml'), info.get('style_type', None)

    if style_file:
        assert (os.path.exists(expected_style_file + '.qml')) == (style_file == 'qml')
        assert (os.path.exists(expected_style_file + '.sld')) == (style_file == 'sld')
    assert (os.path.exists(expected_qgis_file)) == (style == 'qml')
    assert info['style']['type'] == style if style else 'sld', info.get('style')
    assert info['style']['url'], info.get('style')

    response = requests.get(wms_stores_url,
                            auth=settings.LAYMAN_GS_AUTH,
                            timeout=5,
                            )
    assert response.status_code == 200, response.json()
    if style == 'qml':
        wms_stores = [stores['name'] for stores in response.json()['wmsStores']['wmsStore']]
        assert f'{DEFAULT_WMS_QGIS_STORE_PREFIX}_{publication}' in wms_stores, response.json()
    elif style == 'sld':
        url = urljoin(GS_REST, f'workspaces/{workspace}_wms/styles/{publication}')

        response = requests.get(url,
                                auth=GS_AUTH,
                                headers=headers_sld,
                                timeout=5,
                                )
        response.raise_for_status()

    response = requests.get(wms_layers_url,
                            auth=settings.LAYMAN_GS_AUTH,
                            timeout=5,
                            )
    assert response.status_code == 200, response.json()
    if style == 'qml':
        wms_layers = [stores['name'] for stores in response.json()['wmsLayers']['wmsLayer']]
        assert publication in wms_layers, response.json()
