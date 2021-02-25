import requests

import pytest
from layman.util import url_for

import sys

del sys.modules['layman']

from layman.layer import LAYER_TYPE
from layman import app
from layman import settings
from layman import uuid
from .oauth2.util import TOKEN_HEADER, ISS_URL_HEADER
from .oauth2 import liferay
from test import process, process_client


LIFERAY_PORT = process.LIFERAY_PORT

num_layers_before_test = 0


@pytest.fixture(scope="module", autouse=True)
def adjust_settings():
    authn_modules = settings.LAYMAN_AUTHN_MODULES
    settings.LAYMAN_AUTHN_MODULES = [
        'layman.authn.oauth2'
    ]
    yield
    settings.LAYMAN_AUTHN_MODULES = authn_modules


@pytest.fixture()
def unexisting_introspection_url():
    introspection_url = liferay.INTROSPECTION_URL
    liferay.INTROSPECTION_URL = 'http://blabla:8000/bla'
    yield
    liferay.INTROSPECTION_URL = introspection_url


@pytest.fixture()
def inactive_token_introspection_url(liferay_mock):
    introspection_url = liferay.INTROSPECTION_URL
    liferay.INTROSPECTION_URL = f"http://{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{LIFERAY_PORT}/rest/test-oauth2/introspection"
    yield
    liferay.INTROSPECTION_URL = introspection_url


@pytest.fixture()
def active_token_introspection_url(liferay_mock):
    introspection_url = liferay.INTROSPECTION_URL
    liferay.INTROSPECTION_URL = process.AUTHN_INTROSPECTION_URL
    yield
    liferay.INTROSPECTION_URL = introspection_url


@pytest.fixture()
def user_profile_url(liferay_mock):
    user_profile_url = liferay.USER_PROFILE_URL
    liferay.USER_PROFILE_URL = f"http://{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{LIFERAY_PORT}/rest/test-oauth2/user-profile"
    yield
    liferay.USER_PROFILE_URL = user_profile_url


@pytest.fixture(scope="module")
def client():
    client = app.test_client()

    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    app.config['SERVER_NAME'] = settings.LAYMAN_SERVER_NAME
    app.config['SESSION_COOKIE_DOMAIN'] = settings.LAYMAN_SERVER_NAME

    with app.app_context() as ctx:
        publs_by_type = uuid.check_redis_consistency()
        global num_layers_before_test
        num_layers_before_test = len(publs_by_type[LAYER_TYPE])
    yield client


@pytest.fixture()
def app_context():
    with app.app_context() as ctx:
        yield ctx


@pytest.mark.usefixtures('app_context')
def test_two_clients():
    assert len(settings.OAUTH2_LIFERAY_CLIENTS) == 2
    assert isinstance(settings.OAUTH2_LIFERAY_CLIENTS[0]['secret'], str)
    assert settings.OAUTH2_LIFERAY_CLIENTS[1]['secret'] is None


@pytest.mark.usefixtures('app_context')
def test_no_auth_header(client):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username), headers={
        f'{ISS_URL_HEADER}': 'abc'
    })
    assert rv.status_code == 403
    resp_json = rv.get_json()
    assert resp_json['code'] == 32
    assert resp_json['sub_code'] == 2


@pytest.mark.parametrize('headers', [
    {
        f'{ISS_URL_HEADER}': 'abc',
        f'{TOKEN_HEADER}': 'abc',
    }, {
        f'{TOKEN_HEADER}': 'abc',
    }
])
@pytest.mark.usefixtures('app_context')
def test_auth_header_one_part(client, headers):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username), headers=headers)
    assert rv.status_code == 403
    resp_json = rv.get_json()
    assert resp_json['code'] == 32
    assert resp_json['sub_code'] == 3


@pytest.mark.parametrize('headers', [
    {
        f'{ISS_URL_HEADER}': 'abc',
        f'{TOKEN_HEADER}': 'abc abc',
    }, {
        f'{TOKEN_HEADER}': 'abc abc',
    }
])
@pytest.mark.usefixtures('app_context')
def test_auth_header_bad_first_part(client, headers):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username), headers=headers)
    assert rv.status_code == 403
    resp_json = rv.get_json()
    assert resp_json['code'] == 32
    assert resp_json['sub_code'] == 4


@pytest.mark.parametrize('headers', [
    {
        f'{ISS_URL_HEADER}': 'abc',
        f'{TOKEN_HEADER}': 'Bearer ',
    }, {
        f'{TOKEN_HEADER}': 'Bearer ',
    }
])
@pytest.mark.usefixtures('app_context')
def test_auth_header_no_access_token(client, headers):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username), headers=headers)
    assert rv.status_code == 403
    resp_json = rv.get_json()
    assert resp_json['code'] == 32
    assert resp_json['sub_code'] == 5


@pytest.mark.parametrize('headers', [
    {
        f'{ISS_URL_HEADER}': 'abc',
        f'{TOKEN_HEADER}': 'Bearer abc',
    }
])
@pytest.mark.usefixtures('app_context')
def test_no_provider_found(client, headers):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username), headers=headers)
    assert rv.status_code == 403
    resp_json = rv.get_json()
    assert resp_json['code'] == 32
    assert resp_json['sub_code'] == 6


@pytest.mark.parametrize('headers', [
    {
        f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
        f'{TOKEN_HEADER}': 'Bearer abc',
    }, {
        f'{TOKEN_HEADER}': 'Bearer abc',
    }
])
@pytest.mark.usefixtures('app_context', 'unexisting_introspection_url')
def test_unexisting_introspection_url(client, headers):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username), headers=headers)
    assert rv.status_code == 403
    resp_json = rv.get_json()
    assert resp_json['code'] == 32
    assert resp_json['sub_code'] == 8


@pytest.mark.parametrize('headers', [
    {
        f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
        f'{TOKEN_HEADER}': 'Bearer abc',
    }, {
        f'{TOKEN_HEADER}': 'Bearer abc',
    }
])
@pytest.mark.usefixtures('app_context', 'inactive_token_introspection_url', 'ensure_layman')
def test_token_inactive(client, headers):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username), headers=headers)
    assert rv.status_code == 403
    resp_json = rv.get_json()
    assert resp_json['code'] == 32
    assert resp_json['sub_code'] == 9


@pytest.mark.parametrize('headers', [
    {
        f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
        f'{TOKEN_HEADER}': 'Bearer abc',
    }, {
        f'{TOKEN_HEADER}': 'Bearer abc',
    }
])
@pytest.mark.usefixtures('app_context', 'active_token_introspection_url', 'ensure_layman')
def test_token_active(client, headers):
    username = 'testuser1'
    rv = client.get(url_for('rest_layers.get', username=username), headers=headers)
    assert rv.status_code == 404
    resp_json = rv.get_json()
    assert resp_json['code'] == 40


@pytest.mark.usefixtures('app_context', 'active_token_introspection_url', 'user_profile_url', 'ensure_layman')
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
        'preferred_username', 'sub', 'updated_at', 'screen_name'
    } == set(claims.keys())
    assert claims['email'] == 'test@liferay.com'
    assert claims['email_verified'] is True
    assert claims['family_name'] == 'Test'
    assert claims['given_name'] == 'Test'
    assert claims['middle_name'] == ''
    assert claims['name'] == 'Test Test'
    assert claims['preferred_username'] == 'test'
    assert claims['screen_name'] == 'test'
    assert claims['sub'] == '20139'


@pytest.mark.usefixtures('app_context')
def test_get_current_user_anonymous(client):
    rest_path = url_for('rest_current_user.get')
    rv = client.get(rest_path)
    assert rv.status_code == 200
    resp_json = rv.get_json()
    assert resp_json['authenticated'] is False, resp_json
    assert {'authenticated', 'claims'} == set(resp_json.keys()), resp_json
    claims = resp_json['claims']
    assert {
        'iss', 'name', 'nickname'
    } == set(claims.keys()), claims
    assert claims['name'] == 'Anonymous', claims
    assert claims['nickname'] == 'Anonymous', claims


@pytest.mark.usefixtures('app_context')
def test_patch_current_user_anonymous(client):
    rest_path = url_for('rest_current_user.patch')
    rv = client.patch(rest_path)
    assert rv.status_code == 403
    resp_json = rv.get_json()
    assert resp_json['code'] == 30


@pytest.mark.usefixtures('active_token_introspection_url', 'user_profile_url', 'ensure_layman')
def test_patch_current_user_without_username():

    username1 = 'test_patch_current_user_user1'
    username2 = 'test_patch_current_user_user2'

    user1_authn_headers = process_client.get_authz_headers(username1)
    user2_authn_headers = process_client.get_authz_headers(username2)

    # reserve username
    with app.app_context():
        rest_path = url_for('rest_current_user.patch', adjust_username='true')
    r = requests.patch(rest_path, headers=user1_authn_headers)
    assert r.status_code == 200, r.text

    # check if it was reserved
    with app.app_context():
        rest_path = url_for('rest_current_user.get')
    r = requests.get(rest_path, headers=user1_authn_headers)
    assert r.status_code == 200, r.text
    resp_json = r.json()
    assert resp_json['authenticated'] is True
    assert 'username' in resp_json
    exp_username = 'test_patch_current_user_user1_screen_name'
    exp_sub = '20142'
    assert resp_json['username'] == exp_username
    assert resp_json['claims']['sub'] == exp_sub

    iss_id = liferay.__name__
    from layman.authn.redis import _get_issid_sub_2_username_key
    rds_key = _get_issid_sub_2_username_key(iss_id, exp_sub)
    rds = process.LAYMAN_REDIS
    assert rds.get(rds_key) == exp_username

    from layman.authn.filesystem import get_authn_info
    authn_info = get_authn_info(exp_username)
    assert authn_info['iss_id'] == iss_id
    assert authn_info['sub'] == exp_sub

    # re-reserve username
    with app.app_context():
        rest_path = url_for('rest_current_user.patch', adjust_username='true')
    r = requests.patch(rest_path, headers=user1_authn_headers)
    assert r.status_code == 400, r.text
    r_json = r.json()
    assert r_json['code'] == 34
    assert r_json['detail']['username'] == exp_username

    # reserve same username by other user
    with app.app_context():
        rest_path = url_for('rest_current_user.patch')
    r = requests.patch(rest_path, data={
        'username': exp_username,
    }, headers=user2_authn_headers)
    assert r.status_code == 409, r.text
    r_json = r.json()
    assert r_json['code'] == 35
    assert 'detail' not in r_json

    # reserve other username by other user
    with app.app_context():
        rest_path = url_for('rest_current_user.patch')
    exp_username2 = 'test_patch_current_user_user2'
    exp_sub2 = '20143'
    r = requests.patch(rest_path, data={
        'username': exp_username2,
    }, headers=user2_authn_headers)
    assert r.status_code == 200, r.text
    resp_json = r.json()
    assert 'username' in resp_json
    assert resp_json['username'] == exp_username2
    assert resp_json['claims']['sub'] == exp_sub2

    # test map metadata
    workspace = exp_username
    exp_email = 'test_patch_current_user_user1_email' + '@liferay.com'
    exp_name = 'FirstName MiddleName LastName'
    mapname = 'map1'
    process_client.publish_map(workspace, mapname, headers=user1_authn_headers)

    with app.app_context():
        rest_path = url_for('rest_map_file.get', username=workspace, mapname=mapname)
    r = requests.get(rest_path, headers=user1_authn_headers)
    assert r.status_code == 200, r.text
    resp_json = r.json()
    assert resp_json['name'] == mapname
    user_info = resp_json['user']
    assert {'email', 'name'} == set(user_info.keys())
    assert user_info['name'] == exp_name
    assert user_info['email'] == exp_email

    process_client.delete_map(workspace, mapname, headers=user1_authn_headers)
