import os
from multiprocessing import Process
import requests
import time

import pytest
from flask import url_for

import sys

try:
    del sys.modules['layman']
except KeyError:
    pass

from layman.layer import LAYER_TYPE
from layman import app as app
from layman import settings
from layman import uuid
from test import process
from layman.authn.oauth2_test import active_token_introspection_url, user_profile_url
from layman.authn.oauth2 import liferay
from layman.authn.oauth2.util import TOKEN_HEADER, ISS_URL_HEADER


liferay_mock = process.liferay_mock

num_layers_before_test = 0


@pytest.fixture(scope="module", autouse=True)
def adjust_settings():
    authz_module = settings.AUTHZ_MODULE
    settings.AUTHZ_MODULE = 'layman.authz.read_everyone_write_owner'
    authn_modules = settings.LAYMAN_AUTHN_MODULES
    settings.LAYMAN_AUTHN_MODULES = [
        'layman.authn.oauth2'
    ]
    yield
    settings.AUTHZ_MODULE = authz_module
    settings.LAYMAN_AUTHN_MODULES = authn_modules


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


@pytest.fixture()
def app_context():
    with app.app_context() as ctx:
        yield ctx


@pytest.mark.usefixtures('app_context')
def test_anonymous_get_access(client):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username))
    assert rv.status_code == 404
    resp_json = rv.get_json()
    assert resp_json['code'] == 40
    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': num_layers_before_test + 0
    })


@pytest.mark.usefixtures('app_context')
def test_anonymous_post_access(client):
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


@pytest.mark.usefixtures('app_context', 'active_token_introspection_url')
def test_authn_get_access(client):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username), headers={
        f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
        f'{TOKEN_HEADER}': 'Bearer abc',
    })
    assert rv.status_code == 404
    resp_json = rv.get_json()
    assert resp_json['code'] == 40


@pytest.mark.usefixtures('app_context', 'active_token_introspection_url')
def test_authn_post_access_without_username(client):
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
        }, headers={
            f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
            f'{TOKEN_HEADER}': 'Bearer abc',
        })
        assert rv.status_code == 400
        resp_json = rv.get_json()
        assert resp_json['code'] == 33
    finally:
        for fp in files:
            fp[0].close()

    uuid.check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': num_layers_before_test + 0
    })


@pytest.mark.usefixtures('user_profile_url', 'active_token_introspection_url')
def test_authn_map_access_rights(client):
    # reserve username if it's not yet reserved
    with app.app_context():
        rest_path = url_for('rest_current_user.get')
        rv = client.get(rest_path, headers={
            f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
            f'{TOKEN_HEADER}': 'Bearer test2',
        })
        assert rv.status_code == 200
        resp_json = rv.get_json()
    with app.app_context():
        if 'username' not in resp_json:
            rest_path = url_for('rest_current_user.patch', adjust_username='true')
            rv = client.patch(rest_path, headers={
                f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
                f'{TOKEN_HEADER}': 'Bearer test2',
            })
            resp_json = rv.get_json()
            assert rv.status_code == 200
        username = resp_json['username']
        assert username == 'test2'

    # insert map
    mapname = 'map2'
    with app.app_context():
        rest_path = url_for('rest_maps.post', username=username)
        file_paths = [
            'sample/layman.map/full.json',
        ]
        for fp in file_paths:
            assert os.path.isfile(fp)
        files = []
        try:
            files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
            rv = client.post(rest_path, headers={
                f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
                f'{TOKEN_HEADER}': 'Bearer test2',
            }, data={
                'file': files,
                'name': mapname,
            })
            resp_json = rv.get_json()
            # print(resp_json)
            assert rv.status_code == 200
            assert resp_json[0]['name'] == mapname
        finally:
            for fp in files:
                fp[0].close()

    # test map metadata
    with app.app_context():
        rv = client.get(url_for('rest_map_file.get', username=username, mapname=mapname))
        assert rv.status_code == 200
        resp_json = rv.get_json()
        access_rights = resp_json['groups']
        assert {'guest'} == set(access_rights.keys())
        assert access_rights['guest'] == 'r'

    # test non-owner access
    with app.app_context():
        rv = client.patch(url_for('rest_map.patch', username=username, mapname=mapname), headers={
            f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
            f'{TOKEN_HEADER}': 'Bearer test3',
        }, data={
            'title': 'abcd',
        })
        assert rv.status_code == 403
        resp_json = rv.get_json()
        assert resp_json['code'] == 30
        assert resp_json['detail']['username'] in [None, 'test3']
