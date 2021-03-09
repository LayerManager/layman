import requests
import pytest
from lxml import etree as ET

from layman import app
from layman.util import url_for
from test import process_client


@pytest.mark.usefixtures('ensure_layman')
def test_get_layer_style_sld():
    username = 'test_get_layer_style_sld_user'
    layername = 'test_get_layer_style_sld_layer'

    process_client.publish_workspace_layer(username,
                                           layername,
                                           )

    with app.app_context():
        rest_url = url_for('rest_workspace_layer_style.get', username=username, layername=layername)
    rv = requests.get(rest_url)
    assert rv.status_code == 200, rv.text
    # lxml does not support importing from utf8 string
    xml_tree = ET.fromstring(bytes(rv.text, encoding='utf8'))
    assert ET.QName(xml_tree) == "{http://www.opengis.net/sld}StyledLayerDescriptor", rv.text
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
        rest_url = url_for('rest_workspace_layer_style.get', username=username, layername=layername)
    rv = requests.get(rest_url)
    assert rv.status_code == 200, rv.text
    # lxml does not support importing from utf8 string
    xml_el = ET.fromstring(bytes(rv.text, encoding='utf8'))
    assert ET.QName(xml_el), rv.text
    assert ET.QName(xml_el) == "qgis", rv.text
    assert len(xml_el.xpath('/qgis/renderer-v2')) == 1, rv.text
    assert xml_el.attrib, rv.text
    process_client.delete_workspace_layer(username, layername)
