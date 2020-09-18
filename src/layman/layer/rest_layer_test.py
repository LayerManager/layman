from multiprocessing import Process
import requests
import time
from flask import url_for
import pytest

import sys
import os

del sys.modules['layman']

from layman import app
from layman import settings
from layman.layer.rest_test import wait_till_ready
from test import process, client as client_util


@pytest.fixture()
def client():
    client = app.test_client()

    server = Process(target=app.run, kwargs={
        'host': '0.0.0.0',
        'port': settings.LAYMAN_SERVER_NAME.split(':')[1],
        'debug': False,
    })
    server.start()
    time.sleep(1)

    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    app.config['SERVER_NAME'] = settings.LAYMAN_SERVER_NAME
    app.config['SESSION_COOKIE_DOMAIN'] = settings.LAYMAN_SERVER_NAME

    yield client

    server.terminate()
    server.join()


def test_sld_value(client):
    username = 'test_layer_sld_user'
    layername = 'test_layer_sld_layer'

    with app.app_context():
        rest_path = url_for('rest_layers.post', username=username)

        file_paths = [
            'tmp/naturalearth/110m/cultural/ne_110m_populated_places.geojson',
        ]

        for fp in file_paths:
            assert os.path.isfile(fp)
        files = []

        try:
            files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
            rv = client.post(rest_path, data={
                'file': files,
                'name': layername
            })
            assert rv.status_code == 200
        finally:
            for fp in files:
                fp[0].close()

    wait_till_ready(username, layername)

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
