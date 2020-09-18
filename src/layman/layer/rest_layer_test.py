import requests
import sys

del sys.modules['layman']

from layman import app
from test import client as client_util
from layman.util import url_for


client = client_util.client


def test_sld_value(client):
    username = 'test_layer_sld_user'
    layername = 'test_layer_sld_layer'

    client_util.setup_layer_flask(username, layername, client)

    with app.app_context():
        layer_url = url_for('rest_layer.get', username=username, layername=layername)
    r = requests.get(layer_url)
    assert r.status_code == 200, r.json()
    resp_json = r.json()

    assert "sld" in resp_json, r.json()
    assert "url" in resp_json["sld"], r.json()

    sld_url = resp_json["sld"]["url"]

    r_get = requests.get(sld_url)
    assert r_get.status_code == 200, r_get.json()

    r_del = requests.delete(sld_url)
    assert r_del.status_code != 200, r_del.json()

    client_util.delete_layer(username, layername)
