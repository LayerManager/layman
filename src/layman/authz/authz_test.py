import requests
from flask import g
import pytest

from layman import app, settings, LaymanError
from test_tools import process_client
from test_tools.util import url_for
from . import authorize_workspace_publications_decorator


@authorize_workspace_publications_decorator
def mock_method():
    pass


@pytest.mark.parametrize('request_path', [
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/layers',
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/layers/abc',
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/username/abc',
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/username/publications',
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/username/publications/blablabla',
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/username/publications/blablabla/da',
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/users/layers',
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/users/maps/map',
    f'/rest/layers',
    f'/rest/layers/abc',
    f'/rest/username/abc',
    f'/rest/username/publications',
    f'/rest/username/publications/blablabla',
    f'/rest/username/publications/blablabla/da',
    f'/rest/users/layers',
    f'/rest/users/maps/map',
])
def test_authorize_publications_decorator_does_not_accept_path(request_path):
    with app.test_request_context(request_path):
        with pytest.raises(Exception) as exc_info:
            mock_method()
        assert str(exc_info.value) == f"Authorization module is unable to authorize path {request_path}", exc_info.traceback


@pytest.mark.parametrize('request_path', [
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/user_a/layers',
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/user_a/layers/',
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/user_a/maps/',
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/user_a/layers/abc',
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/user_a/layers/some_layer/some/nested/endpoint',
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/user_a/maps/a_map',
    f'/rest/user_a/layers',
    f'/rest/user_a/layers/',
    f'/rest/user_a/maps/',
    f'/rest/user_a/layers/abc',
    f'/rest/user_a/layers/some_layer/some/nested/endpoint',
    f'/rest/user_a/maps/a_map',
])
def test_authorize_publications_decorator_accepts_path(request_path):
    with app.test_request_context(request_path):
        # pylint: disable=assigning-non-slot
        g.user = None
        with pytest.raises(Exception) as exc_info:
            mock_method()
        assert isinstance(exc_info.value, LaymanError), exc_info.traceback


class TestRestApiClass:
    layername = 'test_authorize_decorator_layer'
    mapname = 'test_authorize_decorator_map'
    username = 'test_authorize_decorator_user'
    authz_headers = process_client.get_authz_headers(username)

    @pytest.fixture(scope="class")
    def provide_publications(self):
        username = self.username
        authz_headers = self.authz_headers
        layername = self.layername
        mapname = self.mapname
        process_client.ensure_reserved_username(username, headers=authz_headers)
        process_client.publish_workspace_layer(username, layername, headers=authz_headers)
        process_client.publish_workspace_map(username, mapname, headers=authz_headers)
        yield
        process_client.delete_workspace_layer(username, layername, headers=authz_headers)
        process_client.delete_workspace_map(username, mapname, headers=authz_headers)

    @staticmethod
    def assert_response(response, exp_status_code, exp_data):
        assert response.status_code == exp_status_code, response.text
        if exp_status_code == 200 and exp_data is not None:
            resp_json = response.json()
            if callable(exp_data):
                assert exp_data(resp_json), f"resp_json={resp_json}, exp_data={exp_data}"
            else:
                assert resp_json == exp_data
        elif exp_status_code != 200 and exp_data is not None:
            resp_json = response.json()
            assert resp_json['code'] == exp_data, f"resp_json={resp_json}, exp_data={exp_data}"

    @staticmethod
    def has_single_layer(r_json):
        return {li['name'] for li in r_json} == {TestRestApiClass.layername}

    @staticmethod
    def has_single_map(r_json):
        return {li['name'] for li in r_json} == {TestRestApiClass.mapname}

    @staticmethod
    def has_no_publication(r_json):
        return {li['name'] for li in r_json} == set()

    @pytest.mark.parametrize(
        "rest_action, url_for_params, authz_status_code, authz_response, unauthz_status_code, unauthz_response",
        [
            ('rest_workspace_layers.get', {}, 200, has_single_layer.__func__, 200, has_no_publication.__func__),
            ('rest_workspace_layer.get', {'layername': layername}, 200, None, 404, 15),
            ('rest_workspace_layer_metadata_comparison.get', {'layername': layername}, 200, None, 404, 15),
            ('rest_workspace_layer_style.get', {'layername': layername}, 200, None, 404, 15),
            ('rest_workspace_layer_thumbnail.get', {'layername': layername}, 200, None, 404, 15),
            ('rest_workspace_layer_chunk.get', {'layername': layername}, 400, 20, 404, 15),
            ('rest_workspace_maps.get', {}, 200, has_single_map.__func__, 200, has_no_publication.__func__),
            ('rest_workspace_map.get', {'mapname': mapname}, 200, None, 404, 26),
            ('rest_workspace_map_file.get', {'mapname': mapname}, 200, None, 404, 26),
            ('rest_workspace_map_metadata_comparison.get', {'mapname': mapname}, 200, None, 404, 26),
            ('rest_workspace_map_thumbnail.get', {'mapname': mapname}, 200, None, 404, 26),
        ],
    )
    @pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman', 'provide_publications')
    def test_authorize_publications_decorator_on_rest_api(
            self,
            rest_action,
            url_for_params,
            authz_status_code,
            authz_response,
            unauthz_status_code,
            unauthz_response,
    ):
        username = self.username
        authz_headers = self.authz_headers
        patch_method = None
        publ_name = None
        if '_layer' in rest_action:
            patch_method = process_client.patch_workspace_layer
            publ_name = self.layername
        elif '_map' in rest_action:
            patch_method = process_client.patch_workspace_map
            publ_name = self.mapname
        assert publ_name

        url_for_params['workspace'] = username

        with app.app_context():
            rest_url = url_for(rest_action, **url_for_params)

        patch_method(username, publ_name, headers=authz_headers, access_rights={
            'read': username,
            'write': username,
        })
        response = requests.get(rest_url, headers=authz_headers, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
        self.assert_response(response, authz_status_code, authz_response)
        response = requests.get(rest_url, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
        self.assert_response(response, unauthz_status_code, unauthz_response)

        patch_method(username, publ_name, headers=authz_headers, access_rights={
            'read': settings.RIGHTS_EVERYONE_ROLE,
            'write': settings.RIGHTS_EVERYONE_ROLE,
        })
        response = requests.get(rest_url, headers=authz_headers, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
        self.assert_response(response, authz_status_code, authz_response)
        response = requests.get(rest_url, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
        self.assert_response(response, authz_status_code, authz_response)
