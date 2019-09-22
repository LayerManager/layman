from multiprocessing import Process
import os
import shutil
import time

import pytest
from flask import url_for, Blueprint, jsonify, g, request

import sys
del sys.modules['layman']

from layman.layer import LAYER_TYPE
from layman import app
from layman import settings
from layman import uuid
from .oauth2.util import TOKEN_HEADER, ISS_URL_HEADER
from .oauth2 import liferay
from test.mock.liferay import run


LIFERAY_PORT = 8020


@pytest.fixture(scope="session")
def liferay_mock():
    server = Process(target=run, kwargs={
        'env_vars': {
        },
        'app_config': {
            'ENV': 'development',
            'SERVER_NAME': f'{settings.LAYMAN_DOCKER_MAIN_SERVICE}:{LIFERAY_PORT}',
            'SESSION_COOKIE_DOMAIN': f'{settings.LAYMAN_DOCKER_MAIN_SERVICE}:{LIFERAY_PORT}',
        },
        'host': '0.0.0.0',
        'port': LIFERAY_PORT,
        'debug': True,  # preserve error log in HTTP responses
        'load_dotenv': False,
        'options': {
            'use_reloader': False,
        },
    })
    server.start()
    time.sleep(1)

    yield server

    server.terminate()
    server.join()


PORT = 8000

num_layers_before_test = 0


@pytest.fixture(scope="module", autouse=True)
def adjust_settings():
    authn_modules = settings.AUTHN_MODULES
    settings.AUTHN_MODULES = [
        'layman.authn.oauth2'
    ]
    yield
    settings.AUTHN_MODULES = authn_modules


@pytest.fixture()
def unexisting_introspection_url():
    introspection_url = liferay.INTROSPECTION_URL
    liferay.INTROSPECTION_URL = 'http://blabla:8000/bla'
    yield
    liferay.INTROSPECTION_URL = introspection_url


@pytest.fixture()
def inactive_token_introspection_url(liferay_mock):
    introspection_url = liferay.INTROSPECTION_URL
    liferay.INTROSPECTION_URL = f'http://{settings.LAYMAN_DOCKER_MAIN_SERVICE}:{LIFERAY_PORT}/rest/test-oauth2/introspection'
    yield
    liferay.INTROSPECTION_URL = introspection_url


@pytest.fixture()
def active_token_introspection_url(liferay_mock):
    introspection_url = liferay.INTROSPECTION_URL
    liferay.INTROSPECTION_URL = f'http://{settings.LAYMAN_DOCKER_MAIN_SERVICE}:{LIFERAY_PORT}/rest/test-oauth2/introspection?is_active=true'
    yield
    liferay.INTROSPECTION_URL = introspection_url


@pytest.fixture()
def user_profile_url(liferay_mock):
    user_profile_url = liferay.USER_PROFILE_URL
    liferay.USER_PROFILE_URL = f'http://{settings.LAYMAN_DOCKER_MAIN_SERVICE}:{LIFERAY_PORT}/rest/test-oauth2/user-profile'
    yield
    liferay.USER_PROFILE_URL = user_profile_url


@pytest.fixture(scope="module")
def client():
    client = app.test_client()

    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    app.config['SERVER_NAME'] = f'{settings.LAYMAN_DOCKER_MAIN_SERVICE}:{PORT}'
    app.config['SESSION_COOKIE_DOMAIN'] = f'{settings.LAYMAN_DOCKER_MAIN_SERVICE}:{PORT}'

    with app.app_context() as ctx:
        publs_by_type = uuid.check_redis_consistency()
        global num_layers_before_test
        num_layers_before_test = len(publs_by_type[LAYER_TYPE])
    yield client


@pytest.fixture(scope="module")
def server():
    server = Process(target=app.run, kwargs={
        'host': '0.0.0.0',
        'port': PORT,
        'debug': False,
    })
    server.start()
    time.sleep(1)

    yield server

    server.terminate()
    server.join()


@pytest.fixture()
def app_context():
    with app.app_context() as ctx:
        yield ctx


@pytest.mark.usefixtures('app_context')
def test_no_iss_url_header(client):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username), headers={
        f'{TOKEN_HEADER}': 'abc'
    })
    assert rv.status_code == 403
    resp_json = rv.get_json()
    assert resp_json['code'] == 32
    assert resp_json['detail'] == f'HTTP header {TOKEN_HEADER} was set, but HTTP header {ISS_URL_HEADER} was not found'


@pytest.mark.usefixtures('app_context')
def test_no_auth_header(client):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username), headers={
        f'{ISS_URL_HEADER}': 'abc'
    })
    assert rv.status_code == 403
    resp_json = rv.get_json()
    assert resp_json['code'] == 32
    assert resp_json['detail'] == f'HTTP header {ISS_URL_HEADER} was set, but HTTP header {TOKEN_HEADER} was not found.'


@pytest.mark.usefixtures('app_context')
def test_auth_header_one_part(client):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username), headers={
        f'{ISS_URL_HEADER}': 'abc',
        f'{TOKEN_HEADER}': 'abc',
    })
    assert rv.status_code == 403
    resp_json = rv.get_json()
    assert resp_json['code'] == 32
    assert resp_json['detail'] == f'HTTP header {TOKEN_HEADER} must have 2 parts: "Bearer <access_token>", but has 1 parts.'


@pytest.mark.usefixtures('app_context')
def test_auth_header_bad_first_part(client):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username), headers={
        f'{ISS_URL_HEADER}': 'abc',
        f'{TOKEN_HEADER}': 'abc abc',
    })
    assert rv.status_code == 403
    resp_json = rv.get_json()
    assert resp_json['code'] == 32
    assert resp_json['detail'] == f'First part of HTTP header {TOKEN_HEADER} must be "Bearer", but it\'s abc'


@pytest.mark.usefixtures('app_context')
def test_auth_header_no_access_token(client):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username), headers={
        f'{ISS_URL_HEADER}': 'abc',
        f'{TOKEN_HEADER}': 'Bearer ',
    })
    assert rv.status_code == 403
    resp_json = rv.get_json()
    assert resp_json['code'] == 32
    assert resp_json['detail'] == f'HTTP header {TOKEN_HEADER} contains empty access token. The structure must be "Bearer <access_token>"'


@pytest.mark.usefixtures('app_context')
def test_no_provider_found(client):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username), headers={
        f'{ISS_URL_HEADER}': 'abc',
        f'{TOKEN_HEADER}': 'Bearer abc',
    })
    assert rv.status_code == 403
    resp_json = rv.get_json()
    assert resp_json['code'] == 32
    assert resp_json['detail'] == f'No OAuth2 provider was found for URL passed in HTTP header {ISS_URL_HEADER}.'


@pytest.mark.usefixtures('app_context', 'unexisting_introspection_url')
def test_unexisting_introspection_url(client):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username), headers={
        f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
        f'{TOKEN_HEADER}': 'Bearer abc',
    })
    assert rv.status_code == 403
    resp_json = rv.get_json()
    assert resp_json['code'] == 32
    assert resp_json['detail'] == f'Introspection endpoint is not reachable.'


@pytest.mark.usefixtures('app_context', 'inactive_token_introspection_url', 'server')
def test_token_inactive(client):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username), headers={
        f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
        f'{TOKEN_HEADER}': 'Bearer abc',
    })
    assert rv.status_code == 403
    resp_json = rv.get_json()
    assert resp_json['code'] == 32
    assert resp_json['detail'] == f'Introspection endpoint claims that access token is not active or it\'s not Bearer token.'


@pytest.mark.usefixtures('app_context', 'active_token_introspection_url', 'server')
def test_token_active(client):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username), headers={
        f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
        f'{TOKEN_HEADER}': 'Bearer abc',
    })
    assert rv.status_code == 200


@pytest.mark.usefixtures('app_context', 'active_token_introspection_url', 'user_profile_url', 'server')
def test_authn_get_current_user_without_username(client):
    rest_path = url_for('rest_current_user.get')
    rv = client.get(rest_path, headers={
        f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
        f'{TOKEN_HEADER}': 'Bearer abc',
    })
    assert rv.status_code == 200
    resp_json = rv.get_json()
    assert resp_json['authenticated'] is True
    assert {'authenticated', 'claims'} == set(resp_json.keys())
    claims = resp_json['claims']
    assert {
               'email', 'email_verified', 'family_name', 'given_name', 'iss', 'middle_name', 'name',
               'preferred_username', 'sub', 'updated_at'
           } == set(claims.keys())
    assert claims['email'] == 'test@liferay.com'
    assert claims['email_verified'] is True
    assert claims['family_name'] == 'Test'
    assert claims['given_name'] == 'Test'
    assert claims['middle_name'] == ''
    assert claims['name'] == 'Test Test'
    assert claims['preferred_username'] == 'test'
    assert claims['sub'] == '20139'


@pytest.mark.usefixtures('app_context')
def test_get_current_user_anonymous(client):
    rest_path = url_for('rest_current_user.get')
    rv = client.get(rest_path)
    assert rv.status_code == 200
    resp_json = rv.get_json()
    assert resp_json['authenticated'] is False
    assert {'authenticated', 'claims'} == set(resp_json.keys())
    claims = resp_json['claims']
    assert {
               'iss', 'name', 'nickname'
           } == set(claims.keys())
    assert claims['name'] == 'Anonymous'
    assert claims['nickname'] == 'Anonymous'


@pytest.mark.usefixtures('app_context')
def test_patch_current_user_anonymous(client):
    rest_path = url_for('rest_current_user.patch')
    rv = client.patch(rest_path)
    assert rv.status_code == 403
    resp_json = rv.get_json()
    assert resp_json['code'] == 30


@pytest.mark.usefixtures('active_token_introspection_url', 'user_profile_url', 'server')
def test_patch_current_user_without_username(client):
    # reserve username
    with app.app_context():
        rest_path = url_for('rest_current_user.patch', adjust_username='true')
        rv = client.patch(rest_path, headers={
            f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
            f'{TOKEN_HEADER}': 'Bearer test2',
        })
        assert rv.status_code == 200

    # check if it was reserved
    with app.app_context():
        rest_path = url_for('rest_current_user.get')
        rv = client.get(rest_path, headers={
            f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
            f'{TOKEN_HEADER}': 'Bearer test2',
        })
        assert rv.status_code == 200
        resp_json = rv.get_json()
        assert resp_json['authenticated'] is True
        assert 'username' in resp_json
        exp_username = 'test2'
        exp_sub = '20140'
        assert resp_json['username'] == exp_username
        assert resp_json['claims']['sub'] == exp_sub

        iss_id = liferay.__name__
        from layman.authn.redis import _get_issid_sub_2_username_key
        rds_key = _get_issid_sub_2_username_key(iss_id, exp_sub)
        rds = settings.LAYMAN_REDIS
        assert rds.get(rds_key) == exp_username

        from layman.authn.filesystem import get_authn_info
        authn_info = get_authn_info(exp_username)
        assert authn_info['iss_id'] == iss_id
        assert authn_info['sub'] == exp_sub

    # re-reserve username
    with app.app_context():
        rest_path = url_for('rest_current_user.patch', adjust_username='true')
        rv = client.patch(rest_path, headers={
            f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
            f'{TOKEN_HEADER}': 'Bearer test2',
        })
        assert rv.status_code == 400
        r_json = rv.get_json()
        assert r_json['code'] == 34
        assert r_json['detail']['username'] == exp_username

    # reserve same username by other user
    with app.app_context():
        rest_path = url_for('rest_current_user.patch')
        rv = client.patch(rest_path, data={
            'username': exp_username,
        }, headers={
            f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
            f'{TOKEN_HEADER}': 'Bearer test3',
        })
        assert rv.status_code == 409
        r_json = rv.get_json()
        assert r_json['code'] == 35
        assert 'detail' not in r_json

    # reserve other username by other user
    with app.app_context():
        exp_username2 = 'test3'
        exp_sub2 = '20141'
        rest_path = url_for('rest_current_user.patch')
        rv = client.patch(rest_path, data={
            'username': exp_username2,
        }, headers={
            f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
            f'{TOKEN_HEADER}': 'Bearer test3',
        })
        assert rv.status_code == 200
        resp_json = rv.get_json()
        assert 'username' in resp_json
        assert resp_json['username'] == exp_username2
        assert resp_json['claims']['sub'] == exp_sub2

    # test map metadata
    username = exp_username
    exp_email = 'test2@liferay.com'
    exp_name = 'Test Test'
    mapname = 'map1'
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
            rv = client.post(rest_path, data={
                'file': files,
                'name': mapname,
            })
            assert rv.status_code == 200
            resp_json = rv.get_json()
            assert resp_json[0]['name'] == mapname
        finally:
            for fp in files:
                fp[0].close()

    with app.app_context():
        rv = client.get(url_for('rest_map_file.get', username=username, mapname=mapname))
        assert rv.status_code == 200
        resp_json = rv.get_json()
        assert resp_json['name'] == mapname
        user_info = resp_json['user']
        assert {'email', 'name'} == set(user_info.keys())
        assert user_info['name'] == exp_name
        assert user_info['email'] == exp_email
        # read_everyone_write_everyone
        access_rights = resp_json['groups']
        assert {'guest'} == set(access_rights.keys())
        assert access_rights['guest'] == 'w'


