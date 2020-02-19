from multiprocessing import Process
import pytest
import time

import sys
del sys.modules['layman']

from layman import app as app
from layman import settings
from .csw import get_layer_info


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


@pytest.mark.usefixtures('app_context', 'broken_micka_url')
def test_get_layer_info():
    layer_info = get_layer_info('abc', 'abcd')
    assert layer_info == {}


@pytest.mark.usefixtures('app_context', 'no_micka_url')
def test_get_layer_info():
    layer_info = get_layer_info('abc', 'abcd')
    assert layer_info == {}


