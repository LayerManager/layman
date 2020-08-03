import os
from multiprocessing import Process
import time

import pytest
from flask import url_for

import sys

del sys.modules['layman']

from layman.layer import LAYER_TYPE
from layman import app as app
from layman import settings
from layman import uuid

num_layers_before_test = 0


@pytest.fixture(scope="module", autouse=True)
def adjust_settings():
    authz_module = settings.AUTHZ_MODULE
    settings.AUTHZ_MODULE = 'layman.authz.read_everyone_write_owner'
    yield
    settings.AUTHZ_MODULE = authz_module


@pytest.fixture(scope="module")
def client():
    client = app.test_client()
    server = Process(target=app.run, kwargs={
        'host': '0.0.0.0',
        'port': settings.LAYMAN_SERVER_NAME.split(':')[1],
        'debug': False,
    })
    server.start()
    time.sleep(1)

    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    app.config['SERVER_NAME'] = settings.LAYMAN_SERVER_NAME
    app.config['SESSION_COOKIE_DOMAIN'] = settings.LAYMAN_SERVER_NAME

    with app.app_context() as ctx:
        publs_by_type = uuid.check_redis_consistency()
        global num_layers_before_test
        num_layers_before_test = len(publs_by_type[LAYER_TYPE])
        yield client

    server.terminate()
    server.join()


def test_get_access(client):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username))
    assert rv.status_code == 200
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': num_layers_before_test + 0
    })


def test_post_forbidden_access(client):
    username = 'testuser1'
    rest_path = url_for('rest_layers.post', username=username)
    file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ]
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        rv = client.post(rest_path, data={
            'file': files
        })
        assert rv.status_code == 403
        resp_json = rv.get_json()
        assert resp_json['code'] == 30
        assert resp_json['detail'] == 'authenticated as anonymous user'
        assert resp_json['message'] == 'Unauthorized access'
    finally:
        for fp in files:
            fp[0].close()

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': num_layers_before_test + 0
    })
