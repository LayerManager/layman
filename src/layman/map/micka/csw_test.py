from contextlib import ExitStack
from multiprocessing import Process
import os
import time
import sys
from urllib.parse import urljoin
import requests
from flask import url_for
import pytest

sys.modules.pop('layman', None)

from layman import app, LaymanError
from layman import settings
from layman.map.rest_workspace_test import wait_till_ready
from test_tools.mock.micka import run
from .csw import get_map_info, delete_map, get_metadata_uuid

MICKA_PORT = 8020


def create_server(port):
    server = Process(target=run, kwargs={
        'env_vars': {
            'CSW_GET_RESP_CODE': '500'
        },
        'app_config': {
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


TEST_WORKSPACE = 'testuser_micka'

TEST_MAP = 'samplemap'


@pytest.fixture()
def provide_map(client):
    with app.app_context():
        workspace = TEST_WORKSPACE
        mapname = TEST_MAP
        rest_path = url_for('rest_workspace_maps.post', workspace=workspace)
        file_paths = [
            'sample/layman.map/full.json',
        ]
        for file_path in file_paths:
            assert os.path.isfile(file_path)
        with ExitStack() as stack:
            files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
            response = client.post(rest_path, data={
                'file': files,
                'name': mapname,
            })
        assert response.status_code == 200

    wait_till_ready(workspace, mapname)
    yield response.get_json()[0]
    with app.app_context():
        rest_path = url_for('rest_workspace_map.delete_map', workspace=workspace, mapname=mapname)
        response = client.delete(rest_path)
        assert response.status_code == 200


def patch_map(client):
    with app.app_context():
        workspace = TEST_WORKSPACE
        mapname = TEST_MAP
        rest_path = url_for('rest_workspace_map.patch', workspace=workspace, mapname=mapname)
        file_paths = [
            'sample/layman.map/full.json',
        ]
        for file_path in file_paths:
            assert os.path.isfile(file_path)
        with ExitStack() as stack:
            files = [(stack.enter_context(open(fp, 'rb')), os.path.basename(fp)) for fp in file_paths]
            response = client.patch(rest_path, data={
                'file': files,
                'title': 'patched map',
            })
        assert response.status_code == 200

    wait_till_ready(workspace, mapname)


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
    # pylint: disable=unused-argument
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


@pytest.mark.usefixtures('ensure_layman', 'provide_map', 'broken_micka_url')
def test_delete_map_broken_micka():
    with pytest.raises(LaymanError) as exc_info:
        with app.app_context():
            delete_map(TEST_WORKSPACE, TEST_MAP)
    assert exc_info.value.code == 38


@pytest.mark.usefixtures('app_context', 'broken_micka_url')
def test_get_map_info_broken_micka():
    map_info = get_map_info('abc', 'abcd')
    assert map_info == {}


@pytest.mark.usefixtures('app_context', 'no_micka_url')
def test_get_map_info_no_micka():
    map_info = get_map_info('abc', 'abcd')
    assert map_info == {}


@pytest.mark.usefixtures('ensure_layman', 'provide_map', 'no_micka_url')
def test_delete_map_no_micka():
    with pytest.raises(LaymanError) as exc_info:
        with app.app_context():
            delete_map(TEST_WORKSPACE, TEST_MAP)
    assert exc_info.value.code == 38


@pytest.mark.usefixtures('ensure_layman', 'provide_map')
def test_patch_map_without_metadata(client):
    with app.app_context():
        delete_map(TEST_WORKSPACE, TEST_MAP)
    patch_map(client)


@pytest.mark.usefixtures('ensure_layman')
def test_public_metadata(provide_map):
    uuid = provide_map['uuid']
    muuid = get_metadata_uuid(uuid)
    micka_url = urljoin(settings.CSW_URL, "./")
    response = requests.get(micka_url)
    response.raise_for_status()
    assert muuid in response.text, f"Metadata record {muuid} is not public!"
