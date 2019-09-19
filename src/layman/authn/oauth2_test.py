from multiprocessing import Process
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


introspection_bp = Blueprint('rest_test_oauth2_introspection', __name__)
user_profile_bp = Blueprint('rest_test_oauth2_user_profile', __name__)


@introspection_bp.route('introspection', methods=['POST'])
def post():
    is_active = request.args.get('is_active', None)
    is_active = is_active is not None and is_active.lower() == 'true'

    return jsonify({
        'active': is_active,
        'token_type': 'Bearer',
    }), 200


@user_profile_bp.route('user-profile', methods=['GET'])
def get():
    return jsonify({
        "agreedToTermsOfUse": False,
        "comments": "",
        "companyId": "20099",
        "contactId": "20141",
        "createDate": 1557361648854,
        "defaultUser": False,
        "emailAddress": "test@liferay.com",
        "emailAddressVerified": True,
        "externalReferenceCode": "",
        "facebookId": "0",
        "failedLoginAttempts": 0,
        "firstName": "Test",
        "googleUserId": "",
        "graceLoginCount": 0,
        "greeting": "Welcome Test Test!",
        "jobTitle": "",
        "languageId": "en_US",
        "lastFailedLoginDate": None,
        "lastLoginDate": 1565768756360,
        "lastLoginIP": "172.19.0.1",
        "lastName": "Test",
        "ldapServerId": "-1",
        "lockout": False,
        "lockoutDate": None,
        "loginDate": 1568805421539,
        "loginIP": "172.18.0.1",
        "middleName": "",
        "modifiedDate": 1568805421548,
        "mvccVersion": "11",
        "openId": "",
        "portraitId": "0",
        "reminderQueryAnswer": "aa",
        "reminderQueryQuestion": "what-is-your-father's-middle-name",
        "screenName": "test",
        "status": 0,
        "timeZoneId": "UTC",
        "userId": "20139",
        "uuid": "4ef84411-749a-e617-6191-10e0c6a7147b"
    }), 200


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
def inactive_token_introspection_url():
    introspection_url = liferay.INTROSPECTION_URL
    liferay.INTROSPECTION_URL = url_for('rest_test_oauth2_introspection.post')
    yield
    liferay.INTROSPECTION_URL = introspection_url


@pytest.fixture()
def active_token_introspection_url():
    introspection_url = liferay.INTROSPECTION_URL
    liferay.INTROSPECTION_URL = url_for('rest_test_oauth2_introspection.post', is_active='true')
    yield
    liferay.INTROSPECTION_URL = introspection_url


@pytest.fixture()
def user_profile_url():
    user_profile_url = liferay.USER_PROFILE_URL
    liferay.USER_PROFILE_URL = url_for('rest_test_oauth2_user_profile.get')
    yield
    liferay.USER_PROFILE_URL = user_profile_url


@pytest.fixture(scope="module")
def client():
    app.register_blueprint(introspection_bp, url_prefix='/rest/test-oauth2/')
    app.register_blueprint(user_profile_bp, url_prefix='/rest/test-oauth2/')
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

    # server.terminate()
    # server.join()


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
def test_authn_get_current_user_without_workspace(client):
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
               'preferred_username', 'sub'
           } == set(claims.keys())
    assert claims['email'] == 'test@liferay.com'
    assert claims['email_verified'] is True
    assert claims['family_name'] == 'Test'
    assert claims['given_name'] == 'Test'
    assert claims['middle_name'] == ''
    assert claims['name'] == 'Test Test'
    assert claims['preferred_username'] == 'test'
    assert claims['sub'] == '20139'


@pytest.mark.usefixtures('app_context', 'active_token_introspection_url', 'user_profile_url', 'server')
def test_get_current_user_anonymous(client):
    rest_path = url_for('rest_current_user.get')
    rv = client.get(rest_path)
    assert rv.status_code == 200
    resp_json = rv.get_json()
    print(resp_json)
    assert resp_json['authenticated'] is False
    assert {'authenticated', 'claims'} == set(resp_json.keys())
    claims = resp_json['claims']
    assert {
               'iss', 'name', 'nickname'
           } == set(claims.keys())
    assert claims['name'] == 'Anonymous'
    assert claims['nickname'] == 'Anonymous'
