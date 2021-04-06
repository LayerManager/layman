from multiprocessing import Process
import time
import sys
from test.mock.micka import run
import requests
import pytest

from layman import settings
del sys.modules['layman']


PORT1 = 8020
PORT2 = 8021


def create_server(port, resp_code, env='development'):
    server = Process(target=run, kwargs={
        'env_vars': {
            'CSW_GET_RESP_CODE': str(resp_code)
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
    server = create_server(PORT1, 404)
    server.start()
    time.sleep(1)

    yield server

    server.terminate()
    server.join()


@pytest.fixture(scope="module")
def server2():
    server = create_server(PORT2, 500)
    server.start()
    time.sleep(1)

    yield server

    server.terminate()
    server.join()


@pytest.mark.usefixtures('server', 'server2')
def test_mock():
    csw_url = f"http://{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{PORT1}/csw"
    rv = requests.get(csw_url)
    assert rv.status_code == 404
    assert rv.text == "Response code is 404"

    csw_url = f"http://{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{PORT2}/csw"
    rv = requests.get(csw_url)
    assert rv.status_code == 500
    assert rv.text == "Response code is 500"
