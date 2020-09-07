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
from test import client as client_util


@pytest.fixture(scope="module")
def client():
    # print('before app.test_client()')
    client = app.test_client()

    # print('before Process(target=app.run, kwargs={...')
    server = Process(target=app.run, kwargs={
        'host': '0.0.0.0',
        'port': settings.LAYMAN_SERVER_NAME.split(':')[1],
        'debug': False,
    })
    # print('before server.start()')
    server.start()
    time.sleep(1)

    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    app.config['SERVER_NAME'] = settings.LAYMAN_SERVER_NAME
    app.config['SESSION_COOKIE_DOMAIN'] = settings.LAYMAN_SERVER_NAME

    yield client

    server.terminate()
    server.join()


@pytest.fixture()
def app_context():
    with app.app_context() as ctx:
        yield ctx


@pytest.mark.usefixtures('app_context')
def test_rest_get(client):
    username = 'wfs_proxy_test'
    layername = 'layer_wfs_proxy_test'
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

    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/{username}/wfs?request=Transaction"
    headers = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
    }

    data_xml = client_util.get_wfs_insert_points(username, layername)

    # r = requests.post(rest_url,
    #                   data=data_xml,
    #                   headers=headers)
    # assert r.status_code == 200

    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/wfs?request=GetCapabilities"
    r = requests.post(rest_url,
                      headers=headers)
    assert r.status_code == 200
