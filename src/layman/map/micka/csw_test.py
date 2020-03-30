from flask import url_for
from multiprocessing import Process
import os
import pytest
import time

import sys
del sys.modules['layman']

from layman import app as app, LaymanError
from layman import settings
from .csw import get_map_info, delete_map
from layman.map.rest_test import wait_till_ready


from test.mock.micka import run

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

TEST_MAP = 'samplemap'


@pytest.fixture()
def provide_map(client):
    with app.app_context():
        username = TEST_USER
        mapname = TEST_MAP
        rest_path = url_for('rest_maps.post', username=username)
        file_paths = [
            'sample/layman.map/full.json',
        ]
        for fp in file_paths:
            assert os.path.isfile(fp)
        files = []
        try:
            files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
            rv = client.post(rest_path, data={
                'file': files,
                'name': mapname,
            })
            assert rv.status_code == 200
        finally:
            for fp in files:
                fp[0].close()

    wait_till_ready(username, mapname)
    yield
    with app.app_context():
        rest_path = url_for('rest_map.delete_map', username=username, mapname=mapname)
        rv = client.delete(rest_path)
        assert rv.status_code == 200


def patch_map(client):
    with app.app_context():
        username = TEST_USER
        mapname = TEST_MAP
        rest_path = url_for('rest_map.patch', username=username, mapname=mapname)
        file_paths = [
            'sample/layman.map/full.json',
        ]
        for fp in file_paths:
            assert os.path.isfile(fp)
        files = []
        try:
            files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
            rv = client.patch(rest_path, data={
                'file': files,
                'title': 'patched map',
            })
            assert rv.status_code == 200
        finally:
            for fp in files:
                fp[0].close()

    wait_till_ready(username, mapname)


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

    # print('before server.terminate()')
    server.terminate()
    # print('before server.join()')
    server.join()


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


@pytest.mark.usefixtures('provide_map', 'broken_micka_url')
def test_delete_map_broken_micka():
    with pytest.raises(LaymanError) as exc_info:
        with app.app_context():
            delete_map(TEST_USER, TEST_MAP)
    assert exc_info.value.code == 38


@pytest.mark.usefixtures('app_context', 'broken_micka_url')
def test_get_map_info_broken_micka():
    map_info = get_map_info('abc', 'abcd')
    assert map_info == {}


@pytest.mark.usefixtures('app_context', 'no_micka_url')
def test_get_map_info_no_micka():
    map_info = get_map_info('abc', 'abcd')
    assert map_info == {}


@pytest.mark.usefixtures('provide_map', 'no_micka_url')
def test_delete_map_no_micka():
    with pytest.raises(LaymanError) as exc_info:
        with app.app_context():
            delete_map(TEST_USER, TEST_MAP)
    assert exc_info.value.code == 38


@pytest.mark.usefixtures('provide_map')
def test_patch_map_without_metadata(client):
    with app.app_context():
        delete_map(TEST_USER, TEST_MAP)
    patch_map(client)
