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

from layman import app, LaymanError, celery as celery_util
from layman import settings
from layman.map.map_class import Map
from test_tools.mock.micka import run
from .csw import get_map_info, map_layers_to_operates_on_layers, delete_map
from .. import util

MICKA_PORT = 8020


def wait_till_ready(workspace, mapname):
    chain_info = util.get_map_chain(workspace, mapname)
    while chain_info is not None and not celery_util.is_chain_ready(chain_info):
        time.sleep(0.1)
        chain_info = util.get_map_chain(workspace, mapname)


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
    with app.app_context():
        publication = Map(map_tuple=(workspace, mapname))

    yield publication

    with app.app_context():
        rest_path = url_for('rest_map.delete_map', uuid=publication.uuid)
        response = client.delete(rest_path)
        assert response.status_code == 200


def patch_map(client):
    with app.app_context():
        workspace = TEST_WORKSPACE
        mapname = TEST_MAP
        publication = Map(map_tuple=(workspace, mapname))
        rest_path = url_for('rest_map.patch', uuid=publication.uuid)
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
def test_delete_map_broken_micka(provide_map):
    with pytest.raises(LaymanError) as exc_info:
        with app.app_context():
            delete_map(provide_map)
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
def test_delete_map_no_micka(provide_map):
    with pytest.raises(LaymanError) as exc_info:
        with app.app_context():
            delete_map(provide_map)
    assert exc_info.value.code == 38


@pytest.mark.usefixtures('ensure_layman', 'provide_map')
def test_patch_map_without_metadata(client, provide_map):
    with app.app_context():
        delete_map(provide_map)
    patch_map(client)


@pytest.mark.usefixtures('ensure_layman')
def test_public_metadata(provide_map):
    muuid = provide_map.micka_ids.id
    micka_url = urljoin(settings.CSW_URL, "./")
    response = requests.get(micka_url, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    response.raise_for_status()
    assert muuid in response.text, f"Metadata record {muuid} is not public!"


LAYER1_WS1_IDX0_EXISTING = {
    'name': 'layer1',
    'workspace': 'workspace1',
    'index': 0,
    'uuid': '9cfa8262-9910-4c4c-89a8-c665bcd5b88f',
}
LAYER2_WS1_IDX0_NON_EXISTENT = {
    'name': 'layer2',
    'workspace': 'workspace1',
    'index': 0,
    'uuid': None,
}
LAYER3_WS2_IDX2_EXISTING = {
    'name': 'layer3',
    'workspace': 'workspace2',
    'index': 2,
    'uuid': '36a9dec6-1a99-4ea4-88ef-bd88ba715b4c',
}
LAYER1_WS1_IDX2_EXISTING = {
    'name': 'layer1',
    'workspace': 'workspace1',
    'index': 2,
    'uuid': '9cfa8262-9910-4c4c-89a8-c665bcd5b88f',
}


@pytest.mark.parametrize('map_layers, exp_result', [
    pytest.param([], [], id='empty_list'),
    pytest.param([LAYER1_WS1_IDX0_EXISTING], [LAYER1_WS1_IDX0_EXISTING], id='one_existing_layer'),
    pytest.param([LAYER2_WS1_IDX0_NON_EXISTENT], [], id='one_non_existent_layer'),
    pytest.param([LAYER1_WS1_IDX0_EXISTING, LAYER3_WS2_IDX2_EXISTING],
                 [LAYER1_WS1_IDX0_EXISTING, LAYER3_WS2_IDX2_EXISTING], id='two_existing_layers'),
    pytest.param([LAYER1_WS1_IDX0_EXISTING, LAYER1_WS1_IDX2_EXISTING],
                 [LAYER1_WS1_IDX0_EXISTING], id='one_existing_layer_twice'),
    pytest.param([LAYER1_WS1_IDX2_EXISTING, LAYER3_WS2_IDX2_EXISTING],
                 [LAYER1_WS1_IDX2_EXISTING, LAYER3_WS2_IDX2_EXISTING], id='two_existing_layers_at_same_index'),
    pytest.param(
        [LAYER1_WS1_IDX0_EXISTING, LAYER2_WS1_IDX0_NON_EXISTENT, LAYER3_WS2_IDX2_EXISTING, LAYER1_WS1_IDX2_EXISTING],
        [LAYER1_WS1_IDX0_EXISTING, LAYER3_WS2_IDX2_EXISTING], id='complex'),
])
def test_map_layers_to_operates_on_layers(map_layers, exp_result):
    result = map_layers_to_operates_on_layers(map_layers)
    assert result == exp_result
