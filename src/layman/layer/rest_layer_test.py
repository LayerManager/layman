import sys

del sys.modules['layman']

from layman import app, settings
from test import flask_client
from layman.util import url_for


client = flask_client.client


def test_sld_value(client):
    username = 'test_layer_sld_user'
    layername = 'test_layer_sld_layer'

    flask_client.publish_layer(username, layername, client)

    with app.app_context():
        layer_url = url_for('rest_layer.get', username=username, layername=layername)
        style_url = url_for('rest_layer_style.get', username=username, layername=layername)
        r = client.get(layer_url)
    assert r.status_code == 200, r.get_json()
    resp_json = r.get_json()

    assert "sld" in resp_json, r.get_json()
    assert "url" in resp_json["sld"], r.get_json()
    assert "status" not in resp_json["sld"], r.get_json()

    sld_url = resp_json["sld"]["url"]
    assert sld_url == style_url, (r.get_json(), sld_url)

    with app.app_context():
        r_get = client.get(sld_url)
    assert r_get.status_code == 200, (r_get.get_json(), sld_url)

    with app.app_context():
        r_del = client.delete(sld_url)
    assert r_del.status_code >= 400, (r_del.get_json(), sld_url)

    flask_client.delete_layer(username, layername, client)
