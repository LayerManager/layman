import requests
from lxml import etree as ET

from layman import app
from layman.util import url_for
from test import flask_client as client_util

client = client_util.client


def test_get_layer_style(client):
    username = 'test_get_layer_style_user'
    layername = 'test_get_layer_style_layer'

    client_util.publish_layer(username,
                              layername,
                              client,)

    with app.app_context():
        rest_url = url_for('rest_layer_style.get', username=username, layername=layername)
        rv = client.get(rest_url)
        assert rv.status_code == 200, rv.text
        xml_tree = ET.fromstring(rv.get_data())
        assert ET.QName(xml_tree) == "{http://www.opengis.net/sld}StyledLayerDescriptor", rv.text
    client_util.delete_layer(username, layername, client)
