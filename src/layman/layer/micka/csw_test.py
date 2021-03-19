from flask import url_for
from multiprocessing import Process
import os
import pytest
import time
import requests
from urllib.parse import urljoin

import sys

del sys.modules['layman']

from layman import app, LaymanError
from layman import settings
from .csw import get_layer_info, delete_layer, get_metadata_uuid

from test.mock.micka import run
from test import flask_client

MICKA_PORT = 8020


def create_server(port, env='development'):
    server = Process(target=run, kwargs={
        'env_vars': {
            'CSW_GET_RESP_CODE': '500'
        },
        'app_config': {
            'ENV': env,
            'SERVER_NAME': f"{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{port}",
            'SESSION_COOKIE_DOMAIN': f"{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{port}",
        },
        'host': '0.0.0.0',
        'port': port,
        'debug': True,  # preserve error log in HTTP responses
        'load_dotenv': False,
        'options': {
            'use_reloader': False,
        },
    })
    return server


TEST_USER = 'testuser_micka'

TEST_LAYER = 'ne_110m_admin_0_countries'


@pytest.fixture()
def provide_layer(client):
    username = TEST_USER
    layername = TEST_LAYER
    response = flask_client.publish_layer(username,
                                          layername,
                                          client,)
    yield response

    flask_client.delete_layer(username,
                              layername,
                              client,)


def patch_layer(client):
    username = TEST_USER
    layername = TEST_LAYER
    with app.app_context():
        rest_path = url_for('rest_workspace_layer.patch', username=username, layername=layername)
        file_paths = [
            'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
        ]
        for fp in file_paths:
            assert os.path.isfile(fp)
        files = []
        try:
            files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
            rv = client.patch(rest_path, data={
                'file': files,
                'title': 'patched layer',
            })
            assert rv.status_code == 200
        finally:
            for fp in files:
                fp[0].close()

    flask_client.wait_till_layer_ready(username, layername)


@pytest.fixture(scope="module")
def broken_micka():
    server = create_server(MICKA_PORT)
    server.start()
    time.sleep(1)

    yield server

    server.terminate()
    server.join()


@pytest.fixture(scope="module")
def client():
    # print('before app.test_client()')
    client = app.test_client()

    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    app.config['SERVER_NAME'] = settings.LAYMAN_SERVER_NAME
    app.config['SESSION_COOKIE_DOMAIN'] = settings.LAYMAN_SERVER_NAME

    yield client


@pytest.fixture()
def app_context():
    with app.app_context() as ctx:
        yield ctx


@pytest.fixture()
def broken_micka_url(broken_micka):
    csw_url = settings.CSW_URL
    settings.CSW_URL = f"http://{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{MICKA_PORT}/csw"
    yield
    settings.CSW_URL = csw_url


@pytest.fixture()
def no_micka_url():
    csw_url = settings.CSW_URL
    settings.CSW_URL = f"http://unexistinghost/cswa"
    yield
    settings.CSW_URL = csw_url


@pytest.mark.usefixtures('ensure_layman', 'provide_layer', 'broken_micka_url')
def test_delete_layer_broken_micka():
    with pytest.raises(LaymanError) as exc_info:
        with app.app_context():
            delete_layer(TEST_USER, TEST_LAYER)
    assert exc_info.value.code == 38


@pytest.mark.usefixtures('app_context', 'broken_micka_url')
def test_get_layer_info_broken_micka():
    layer_info = get_layer_info('abc', 'abcd')
    assert layer_info == {}


@pytest.mark.usefixtures('app_context', 'no_micka_url')
def test_get_layer_info_no_micka():
    layer_info = get_layer_info('abc', 'abcd')
    assert layer_info == {}


@pytest.mark.usefixtures('ensure_layman', 'provide_layer', 'no_micka_url')
def test_delete_layer_no_micka():
    with pytest.raises(LaymanError) as exc_info:
        with app.app_context():
            delete_layer(TEST_USER, TEST_LAYER)
    assert exc_info.value.code == 38


@pytest.mark.usefixtures('ensure_layman', 'provide_layer')
def test_patch_layer_without_metadata(client):
    with app.app_context():
        delete_layer(TEST_USER, TEST_LAYER)
    patch_layer(client)


@pytest.mark.usefixtures('ensure_layman')
def test_public_metadata(provide_layer):
    uuid = provide_layer['uuid']
    muuid = get_metadata_uuid(uuid)
    micka_url = urljoin(settings.CSW_URL, "./")
    r = requests.get(micka_url)
    r.raise_for_status()
    assert muuid in r.text, f"Metadata record {muuid} is not public!"
