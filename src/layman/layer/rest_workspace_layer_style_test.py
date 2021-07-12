import requests
from lxml import etree as ET
import pytest

from layman import app
from test_tools import process_client
from test_tools.util import url_for


@pytest.mark.usefixtures('ensure_layman')
def test_get_layer_style_sld():
    username = 'test_get_layer_style_sld_user'
    layername = 'test_get_layer_style_sld_layer'

    process_client.publish_workspace_layer(username,
                                           layername,
                                           )

    with app.app_context():
        rest_url = url_for('rest_workspace_layer_style.get', workspace=username, layername=layername)
    response = requests.get(rest_url)
    assert response.status_code == 200, response.text
    # lxml does not support importing from utf8 string
    xml_tree = ET.fromstring(bytes(response.text, encoding='utf8'))
    assert ET.QName(xml_tree) == "{http://www.opengis.net/sld}StyledLayerDescriptor", response.text
    process_client.delete_workspace_layer(username, layername)


@pytest.mark.usefixtures('ensure_layman')
def test_get_layer_style_qml():
    username = 'test_get_layer_style_sld_user'
    layername = 'test_get_layer_style_sld_layer'
    qml_file = 'sample/style/small_layer.qml'

    process_client.publish_workspace_layer(username,
                                           layername,
                                           style_file=qml_file
                                           )

    with app.app_context():
        rest_url = url_for('rest_workspace_layer_style.get', workspace=username, layername=layername)
    response = requests.get(rest_url)
    assert response.status_code == 200, response.text
    # lxml does not support importing from utf8 string
    xml_el = ET.fromstring(bytes(response.text, encoding='utf8'))
    assert ET.QName(xml_el), response.text
    assert ET.QName(xml_el) == "qgis", response.text
    assert len(xml_el.xpath('/qgis/renderer-v2')) == 1, response.text
    assert xml_el.attrib, response.text
    process_client.delete_workspace_layer(username, layername)
