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

liferay_mock = process.liferay_mock

LIFERAY_PORT = process.LIFERAY_PORT

ISS_URL_HEADER = client_util.ISS_URL_HEADER
TOKEN_HEADER = client_util.TOKEN_HEADER

AUTHN_INTROSPECTION_URL = process.AUTHN_INTROSPECTION_URL
AUTHN_SETTINGS = process.AUTHN_SETTINGS


@pytest.fixture()
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


def test_rest_get(client):
    username = 'wfs_proxy_test'
    layername = 'layer_wfs_proxy_test'

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

    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/{username}/wfs?request=Transaction"
    headers = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
    }

    data_xml = client_util.get_wfs_insert_points(username, layername)

    with app.app_context():
        r = client.post(rest_url,
                        data=data_xml,
                        headers=headers)
    assert r.status_code == 200

    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/wfs?request=GetCapabilities"
    with app.app_context():
        r = client.post(rest_url,
                        headers=headers)
    assert r.status_code == 200

    with app.app_context():
        rest_path = url_for('rest_layer.delete_layer', username=username, layername=layername)
        client.delete(rest_path)
        assert rv.status_code == 200


def test_wfs_proxy(liferay_mock):
    username = 'testproxy'
    layername1 = 'ne_countries'
    username2 = 'testproxy2'

    layman_process = process.start_layman(dict({
        'LAYMAN_AUTHZ_MODULE': 'layman.authz.read_everyone_write_owner',
    }, **AUTHN_SETTINGS))

    authn_headers1 = {
        f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
        f'{TOKEN_HEADER}': f'Bearer {username}',
    }

    client_util.reserve_username(username, headers=authn_headers1)
    ln = client_util.publish_layer(username, layername1, [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ], headers=authn_headers1)

    assert ln == layername1

    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/{username}/wfs?request=Transaction"
    headers = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
        **authn_headers1,
    }

    data_xml = client_util.get_wfs_insert_points(username, layername1)

    r = requests.post(rest_url,
                      data=data_xml,
                      headers=headers)
    assert r.status_code == 200, r.text

    # Testing, that user2 is not able to write to layer of user1
    authn_headers2 = {
        f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
        f'{TOKEN_HEADER}': f'Bearer {username2}',
    }

    headers2 = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
        **authn_headers2,
    }

    client_util.reserve_username(username2, headers=authn_headers2)

    r = requests.post(rest_url,
                      data=data_xml,
                      headers=headers2)
    assert r.status_code == 400

    # Test anonymous
    headers3 = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
    }

    r = requests.post(rest_url,
                      data=data_xml,
                      headers=headers3)
    assert r.status_code == 400

    # Test fraud header
    headers4 = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
        settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE: username,
    }

    print(headers4)
    r = requests.post(rest_url,
                      data=data_xml,
                      headers=headers4)
    assert r.status_code == 400

    process.stop_process(layman_process)
