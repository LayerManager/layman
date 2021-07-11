from multiprocessing import Process
import time
import sys
from test_tools.mock.liferay import run
import requests
import pytest

from layman import settings

del sys.modules['layman']
from .util import TOKEN_HEADER, ISS_URL_HEADER

PORT1 = 8031
PORT2 = 8032


def create_server(port, env='development'):
    server = Process(target=run, kwargs={
        'env_vars': {
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
def server():
    server = create_server(PORT1)
    server.start()
    time.sleep(1)

    yield server

    server.terminate()
    server.join()


@pytest.fixture(scope="module")
def server2():
    server = create_server(PORT2, env='production')
    server.start()
    time.sleep(1)

    yield server

    server.terminate()
    server.join()


@pytest.mark.usefixtures('server', 'server2')
def test_mock():
    url1 = f"http://{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{PORT1}/rest/test-oauth2/user-profile"
    response = requests.get(url1, headers={
        f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
        f'{TOKEN_HEADER}': 'Bearer abc'
    })
    assert response.status_code == 200
    resp_json = response.json()
    assert resp_json['FLASK_ENV'] == 'development'

    url2 = f"http://{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{PORT2}/rest/test-oauth2/user-profile"
    response = requests.get(url2, headers={
        f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
        f'{TOKEN_HEADER}': 'Bearer abc'
    })
    assert response.status_code == 200
    resp_json = response.json()
    assert resp_json['FLASK_ENV'] == 'production'
