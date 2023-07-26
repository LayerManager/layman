import sys
import requests
import pytest

del sys.modules['layman']

from layman import app
from layman import settings
from test_tools import process, process_client
from test_tools.util import url_for
from .oauth2 import TOKEN_HEADER
from . import oauth2


OAUTH2_PROVIDER_MOCK_PORT = process.OAUTH2_PROVIDER_MOCK_PORT


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
    introspection_url = oauth2.INTROSPECTION_URL
    oauth2.INTROSPECTION_URL = 'http://blabla:8000/bla'
    yield
    oauth2.INTROSPECTION_URL = introspection_url


@pytest.fixture()
def inactive_token_introspection_url(oauth2_provider_mock):
    # pylint: disable=unused-argument
    introspection_url = oauth2.INTROSPECTION_URL
    oauth2.INTROSPECTION_URL = f"http://{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{OAUTH2_PROVIDER_MOCK_PORT}/rest/test-oauth2/introspection"
    yield
    oauth2.INTROSPECTION_URL = introspection_url


@pytest.fixture()
def active_token_introspection_url(oauth2_provider_mock):
    # pylint: disable=unused-argument
    introspection_url = oauth2.INTROSPECTION_URL
    oauth2.INTROSPECTION_URL = process.AUTHN_INTROSPECTION_URL
    yield
    oauth2.INTROSPECTION_URL = introspection_url


@pytest.fixture()
def user_profile_url(oauth2_provider_mock):
    # pylint: disable=unused-argument
    user_profile_url = oauth2.USER_PROFILE_URL
    oauth2.USER_PROFILE_URL = f"http://{settings.LAYMAN_SERVER_NAME.split(':')[0]}:{OAUTH2_PROVIDER_MOCK_PORT}/rest/test-oauth2/user-profile"
    yield
    oauth2.USER_PROFILE_URL = user_profile_url


@pytest.fixture(scope="module")
def client():
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


@pytest.mark.usefixtures('app_context')
def test_two_clients():
    assert len(settings.OAUTH2_CLIENTS) == 2
    assert isinstance(settings.OAUTH2_CLIENTS[0]['secret'], str)
    assert settings.OAUTH2_CLIENTS[1]['secret'] is None


@pytest.mark.parametrize('headers', [
    {
        f'{TOKEN_HEADER}': 'abc',
    }
])
@pytest.mark.usefixtures('app_context')
def test_auth_header_one_part(client, headers):
    username = 'testuser1'
    response = client.get(url_for('rest_workspace_layers.get', workspace=username), headers=headers)
    assert response.status_code == 403
    resp_json = response.get_json()
    assert resp_json['code'] == 32
    assert resp_json['sub_code'] == 3


@pytest.mark.parametrize('headers', [
    {
        f'{TOKEN_HEADER}': 'abc abc',
    }
])
@pytest.mark.usefixtures('app_context')
def test_auth_header_bad_first_part(client, headers):
    username = 'testuser1'
    response = client.get(url_for('rest_workspace_layers.get', workspace=username), headers=headers)
    assert response.status_code == 403
    resp_json = response.get_json()
    assert resp_json['code'] == 32
    assert resp_json['sub_code'] == 4


@pytest.mark.parametrize('headers', [
    {
        f'{TOKEN_HEADER}': 'Bearer ',
    }
])
@pytest.mark.usefixtures('app_context')
def test_auth_header_no_access_token(client, headers):
    username = 'testuser1'
    response = client.get(url_for('rest_workspace_layers.get', workspace=username), headers=headers)
    assert response.status_code == 403
    resp_json = response.get_json()
    assert resp_json['code'] == 32
    assert resp_json['sub_code'] == 5


@pytest.mark.parametrize('headers', [
    {
        f'{TOKEN_HEADER}': 'Bearer abc',
    }
])
@pytest.mark.usefixtures('app_context', 'unexisting_introspection_url')
def test_unexisting_introspection_url(client, headers):
    username = 'testuser1'
    response = client.get(url_for('rest_workspace_layers.get', workspace=username), headers=headers)
    assert response.status_code == 403
    resp_json = response.get_json()
    assert resp_json['code'] == 32
    assert resp_json['sub_code'] == 8


@pytest.mark.parametrize('headers', [
    {
        f'{TOKEN_HEADER}': 'Bearer abc',
    }
])
@pytest.mark.usefixtures('app_context', 'inactive_token_introspection_url', 'ensure_layman')
def test_token_inactive(client, headers):
    username = 'testuser1'
    url = url_for('rest_workspace_layers.get', workspace=username)
    response = client.get(url, headers=headers)
    assert response.status_code == 403
    resp_json = response.get_json()
    assert resp_json['code'] == 32
    assert resp_json['sub_code'] == 9


@pytest.mark.parametrize('headers', [
    {
        f'{TOKEN_HEADER}': 'Bearer abc',
    }
])
@pytest.mark.usefixtures('app_context', 'active_token_introspection_url', 'ensure_layman')
def test_token_active(client, headers):
    username = 'testuser1'
    url = url_for('rest_workspace_layers.get', workspace=username)
    response = client.get(url, headers=headers)
    assert response.status_code == 404
    resp_json = response.get_json()
    assert resp_json['code'] == 40


@pytest.mark.usefixtures('app_context', 'active_token_introspection_url', 'user_profile_url', 'ensure_layman')
def test_authn_get_current_user_without_username(client):
    rest_path = url_for('rest_current_user.get')
    response = client.get(rest_path, headers={
        f'{TOKEN_HEADER}': 'Bearer abc',
    })
    assert response.status_code == 200
    resp_json = response.get_json()
    assert resp_json['authenticated'] is True
    assert {'authenticated', 'claims'} == set(resp_json.keys())
    claims = resp_json['claims']
    assert {
        'email', 'family_name', 'given_name', 'iss', 'middle_name', 'name',
        'preferred_username', 'sub', 'screen_name'
    } == set(claims.keys())
    assert claims['email'] == 'test@oauth2.org'
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
    response = client.get(rest_path)
    assert response.status_code == 200
    resp_json = response.get_json()
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
    response = client.patch(rest_path)
    assert response.status_code == 403
    resp_json = response.get_json()
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
    response = requests.patch(rest_path, headers=user1_authn_headers, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    assert response.status_code == 200, response.text

    # check if it was reserved
    with app.app_context():
        rest_path = url_for('rest_current_user.get')
    response = requests.get(rest_path, headers=user1_authn_headers, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    assert response.status_code == 200, response.text
    resp_json = response.json()
    assert resp_json['authenticated'] is True
    assert 'username' in resp_json
    exp_username = 'test_patch_current_user_user1_screen_name'
    exp_sub = '20142'
    assert resp_json['username'] == exp_username
    assert resp_json['claims']['sub'] == exp_sub

    iss_id = 'layman.authn.oauth2'
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
    response = requests.patch(rest_path, headers=user1_authn_headers, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    assert response.status_code == 400, response.text
    r_json = response.json()
    assert r_json['code'] == 34
    assert r_json['detail']['username'] == exp_username

    # reserve same username by other user
    with app.app_context():
        rest_path = url_for('rest_current_user.patch')
    response = requests.patch(rest_path, data={
        'username': exp_username,
    }, headers=user2_authn_headers, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    assert response.status_code == 409, response.text
    r_json = response.json()
    assert r_json['code'] == 35
    assert 'detail' not in r_json

    # reserve other username by other user
    with app.app_context():
        rest_path = url_for('rest_current_user.patch')
    exp_username2 = 'test_patch_current_user_user2'
    exp_sub2 = '20143'
    response = requests.patch(rest_path, data={
        'username': exp_username2,
    }, headers=user2_authn_headers, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    assert response.status_code == 200, response.text
    resp_json = response.json()
    assert 'username' in resp_json
    assert resp_json['username'] == exp_username2
    assert resp_json['claims']['sub'] == exp_sub2

    # test map metadata
    workspace = exp_username
    exp_email = 'test_patch_current_user_user1_email' + '@oauth2.org'
    exp_name = 'FirstName MiddleName LastName'
    mapname = 'map1'
    process_client.publish_workspace_map(workspace, mapname, headers=user1_authn_headers)

    with app.app_context():
        rest_path = url_for('rest_workspace_map_file.get', workspace=workspace, mapname=mapname)
    response = requests.get(rest_path, headers=user1_authn_headers, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    assert response.status_code == 200, response.text
    resp_json = response.json()
    assert resp_json['name'] == mapname
    user_info = resp_json['user']
    assert {'email', 'name'} == set(user_info.keys())
    assert user_info['name'] == exp_name
    assert user_info['email'] == exp_email

    process_client.delete_workspace_map(workspace, mapname, headers=user1_authn_headers)
