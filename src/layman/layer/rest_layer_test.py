import requests


from layman.util import url_for
from test import process, client as client_util
from layman import app

layman_fixture = process.layman_fixture


def test_sld_value(layman_fixture):
    username = 'test_layer_sld_user'
    layername = 'test_layer_sld_layer'

    ln = client_util.publish_layer(username, layername, [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ])
    assert ln == layername

    with app.app_context():
        layer_url = url_for('rest_layer.get', username=username, layername=layername)
    r = requests.get(layer_url)
    assert r.status_code == 200, r.json()
    print(f"Text:{r.text}")
    resp_json = r.json()

    assert "sld" in resp_json, r.json()
    assert "url" in resp_json["sld"], r.json()

    sld_url = resp_json["sld"]["url"]

    r = requests.get(sld_url)
    assert r.status_code == 200, r.json()

    r = requests.delete(sld_url)
    assert r.status_code != 200, r.json()
