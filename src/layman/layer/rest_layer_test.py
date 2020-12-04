import sys
import pytest
import requests
import json

del sys.modules['layman']

from layman import app
from test import process, process_client
from layman.util import url_for

ensure_layman = process.ensure_layman


@pytest.mark.usefixtures('ensure_layman')
def test_sld_value():
    username = 'test_layer_sld_user'
    layername = 'test_layer_sld_layer'

    process_client.publish_layer(username, layername)

    with app.app_context():
        layer_url = url_for('rest_layer.get', username=username, layername=layername)
        style_url = url_for('rest_layer_style.get', username=username, layername=layername)
    r = requests.get(layer_url)
    assert r.status_code == 200, r.text
    resp_json = json.loads(r.text)

    assert "sld" in resp_json, r.text
    assert "url" in resp_json["sld"], r.text
    assert "status" not in resp_json["sld"], r.text

    sld_url = resp_json["sld"]["url"]
    assert sld_url == style_url, (r.text, sld_url)

    r_get = requests.get(sld_url)
    assert r_get.status_code == 200, (r_get.text, sld_url)

    r_del = requests.delete(sld_url)
    assert r_del.status_code >= 400, (r_del.text, sld_url)

    process_client.delete_layer(username, layername)
