import json
import pytest
import requests

from layman import app, settings, LaymanError
from layman.util import url_for
from flask import g
from . import authorize_publications_decorator
from test import process, process_client


liferay_mock = process.liferay_mock
ensure_auth_layman = process.ensure_auth_layman


@authorize_publications_decorator
def mock_method():
    pass


@pytest.mark.parametrize('request_path', [
    '/rest/layers',
    '/rest/layers/abc',
    '/rest/username/abc',
    '/rest/username/publications',
    '/rest/username/publications/blablabla',
    '/rest/username/publications/blablabla/da',
    '/rest/users/layers',
    '/rest/users/maps/map',
])
def test_authorize_publications_decorator_does_not_accept_path(request_path):
    with app.test_request_context(request_path):
        with pytest.raises(Exception) as exc_info:
            mock_method()
        assert str(exc_info.value) == f"Authorization module is unable to authorize path {request_path}", exc_info.traceback


@pytest.mark.parametrize('request_path', [
    '/rest/user_a/layers',
    '/rest/user_a/layers/',
    '/rest/user_a/maps/',
    '/rest/user_a/layers/abc',
    '/rest/user_a/layers/some_layer/some/nested/endpoint',
    '/rest/user_a/maps/a_map',
])
def test_authorize_publications_decorator_accepts_path(request_path):
    with app.test_request_context(request_path):
        g.user = None
        with pytest.raises(Exception) as exc_info:
            mock_method()
        assert isinstance(exc_info.value, LaymanError)


layername = 'test_authorize_decorator_layer'
username = 'test_authorize_decorator_user'
user_authz_headers = process_client.get_authz_headers(username)


@pytest.fixture(scope="module")
def provide_user_and_layer(username=username, layername=layername, authz_headers=user_authz_headers):
    process_client.ensure_reserved_username(username, headers=authz_headers)
    process_client.publish_layer(username, layername, headers=authz_headers)
    yield
    process_client.delete_layer(username, layername, headers=authz_headers)


@pytest.mark.parametrize(
    "rest_action, url_for_params, authz_status_code, authz_response, unauthz_status_code, unauthz_response",
    [
        ('rest_layers.get', {}, 200, lambda r_json: {li['name'] for li in r_json} == {layername},
            200, lambda r_json: {li['name'] for li in r_json} == set()),
        ('rest_layer.get', {'layername': layername}, 200, None, 404, 15),
        ('rest_layer_metadata_comparison.get', {'layername': layername}, 200, None, 404, 15),
        ('rest_layer_style.get', {'layername': layername}, 200, None, 404, 15),
        ('rest_layer_thumbnail.get', {'layername': layername}, 200, None, 404, 15),
        ('rest_layer_chunk.get', {'layername': layername}, 400, 20, 404, 15),
    ],
)
@pytest.mark.usefixtures('liferay_mock', 'ensure_auth_layman', 'provide_user_and_layer')
def test_authorize_publications_decorator_on_rest_api(
        rest_action,
        url_for_params,
        authz_status_code,
        authz_response,
        unauthz_status_code,
        unauthz_response,
        username=username,
        layername=layername,
        authz_headers=user_authz_headers,
):
    def assert_response(response, exp_status_code, exp_data):
        assert response.status_code == exp_status_code, r.text
        if exp_status_code == 200 and exp_data is not None:
            resp_json = response.json()
            if callable(exp_data):
                assert exp_data(resp_json), exp_data
            else:
                assert resp_json == exp_data
        elif exp_status_code != 200 and exp_data is not None:
            resp_json = response.json()
            assert resp_json['code'] == exp_data

    url_for_params['username'] = username

    with app.app_context():
        rest_url = url_for(rest_action, **url_for_params)

    process_client.patch_layer(username, layername, headers=authz_headers, access_rights={
        'read': username,
        'write': username,
    })
    r = requests.get(rest_url, headers=authz_headers)
    assert_response(r, authz_status_code, authz_response)
    r = requests.get(rest_url)
    assert_response(r, unauthz_status_code, unauthz_response)

    process_client.patch_layer(username, layername, headers=authz_headers, access_rights={
        'read': settings.RIGHTS_EVERYONE_ROLE,
        'write': settings.RIGHTS_EVERYONE_ROLE,
    })
    r = requests.get(rest_url, headers=authz_headers)
    assert_response(r, authz_status_code, authz_response)
    r = requests.get(rest_url)
    assert_response(r, authz_status_code, authz_response)



publication_name = 'test_public_workspace_variable_publication'
username = 'test_public_workspace_variable_user'
workspace_name = 'test_public_workspace_variable_workspace'
user_authz_headers = process_client.get_authz_headers(username)


@pytest.fixture(scope="module")
def setup_test_public_workspace_variable(username=username):
    env_vars = dict(process.AUTHN_SETTINGS)

    layman_process = process.start_layman(env_vars)
    process_client.reserve_username(username, headers=user_authz_headers)
    process.stop_process(layman_process)
    yield


@pytest.mark.usefixtures('liferay_mock', 'setup_test_public_workspace_variable')
@pytest.mark.parametrize(
    "create_public_workspace, publish_in_public_workspace, workspace_prefix, publication_name, authz_headers,"
    "user_can_create, anonymous_can_publish, anonymous_can_create,",
    [
        ('EVERYONE', 'EVERYONE', workspace_name + 'ee', publication_name, user_authz_headers, True, True, True,),
        (username, username, workspace_name + 'uu', publication_name, user_authz_headers, True, False, False,),
        ('', '', workspace_name + 'nn', publication_name, user_authz_headers, False, False, False,),
        (username, 'EVERYONE', workspace_name + 'ue', publication_name, user_authz_headers, True, True, False,),
    ],
)
@pytest.mark.parametrize("publish_method, delete_method, workspace_suffix", [
    (process_client.publish_layer, process_client.delete_layer, '_layer',),
    (process_client.publish_map, process_client.delete_map, '_map',),
])
def test_public_workspace_variable(create_public_workspace,
                                   publish_in_public_workspace,
                                   workspace_prefix,
                                   publication_name,
                                   authz_headers,
                                   user_can_create,
                                   anonymous_can_publish,
                                   anonymous_can_create,
                                   publish_method,
                                   delete_method,
                                   workspace_suffix,
                                   ):
    def can_not_publish(workspace_name,
                        publication_name,
                        publish_method,
                        authz_headers=None,
                        ):
        r = publish_method(workspace_name,
                           publication_name,
                           headers=authz_headers,
                           assert_status=False)
        assert r.status_code == 403
        details = json.loads(r.text)
        assert details['code'] == 30
        assert details['message'] == "Unauthorized access"

    workspace_name = workspace_prefix + workspace_suffix
    workspace_name2 = workspace_name + '2'
    layername2 = publication_name + '2'
    env_vars = dict(process.AUTHN_SETTINGS)
    env_vars['GRANT_CREATE_PUBLIC_WORKSPACE'] = create_public_workspace
    env_vars['GRANT_PUBLISH_IN_PUBLIC_WORKSPACE'] = publish_in_public_workspace
    layman_process = process.start_layman(env_vars)

    if user_can_create:
        publish_method(workspace_name, publication_name, headers=authz_headers)
        if anonymous_can_publish:
            publish_method(workspace_name, layername2)
            delete_method(workspace_name, layername2)
        delete_method(workspace_name, publication_name, headers=authz_headers)
    else:
        can_not_publish(workspace_name, publication_name, publish_method, authz_headers)

    if anonymous_can_create:
        publish_method(workspace_name2, publication_name)
        delete_method(workspace_name2, publication_name)
    else:
        can_not_publish(workspace_name2, publication_name, publish_method)

    process.stop_process(layman_process)
