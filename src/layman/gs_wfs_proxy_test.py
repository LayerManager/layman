from multiprocessing import Process
import requests
import time

import pytest

import sys

del sys.modules['layman']

from layman import app as app
from layman import settings


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
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest/wfs-proxy"
    headers = {'Accept': 'application/json',
               'Content-type': 'application/json',
               }
    r = requests.get(rest_url,
                     headers=headers)
    assert r.status_code == 200
