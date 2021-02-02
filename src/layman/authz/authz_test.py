import pytest
import requests

from layman import app, settings, LaymanError
from layman.util import url_for
from flask import g
from . import authorize_publications_decorator
from test import process_client


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
        process_client.publish_layer(username, layername, headers=authz_headers)
        process_client.publish_map(username, mapname, headers=authz_headers)
        yield
        process_client.delete_layer(username, layername, headers=authz_headers)
        process_client.delete_map(username, mapname, headers=authz_headers)

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
            ('rest_layers.get', {}, 200, has_single_layer.__func__, 200, has_no_publication.__func__),
            ('rest_layer.get', {'layername': layername}, 200, None, 404, 15),
            ('rest_layer_metadata_comparison.get', {'layername': layername}, 200, None, 404, 15),
            ('rest_layer_style.get', {'layername': layername}, 200, None, 404, 15),
            ('rest_layer_thumbnail.get', {'layername': layername}, 200, None, 404, 15),
            ('rest_layer_chunk.get', {'layername': layername}, 400, 20, 404, 15),
            ('rest_maps.get', {}, 200, has_single_map.__func__, 200, has_no_publication.__func__),
            ('rest_map.get', {'mapname': mapname}, 200, None, 404, 26),
            ('rest_map_file.get', {'mapname': mapname}, 200, None, 404, 26),
            ('rest_map_metadata_comparison.get', {'mapname': mapname}, 200, None, 404, 26),
            ('rest_map_thumbnail.get', {'mapname': mapname}, 200, None, 404, 26),
        ],
    )
    @pytest.mark.usefixtures('liferay_mock', 'ensure_layman', 'provide_publications')
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
            patch_method = process_client.patch_layer
            publ_name = self.layername
        elif '_map' in rest_action:
            patch_method = process_client.patch_map
            publ_name = self.mapname
        assert publ_name

        url_for_params['username'] = username

        with app.app_context():
            rest_url = url_for(rest_action, **url_for_params)

        patch_method(username, publ_name, headers=authz_headers, access_rights={
            'read': username,
            'write': username,
        })
        r = requests.get(rest_url, headers=authz_headers)
        self.assert_response(r, authz_status_code, authz_response)
        r = requests.get(rest_url)
        self.assert_response(r, unauthz_status_code, unauthz_response)

        patch_method(username, publ_name, headers=authz_headers, access_rights={
            'read': settings.RIGHTS_EVERYONE_ROLE,
            'write': settings.RIGHTS_EVERYONE_ROLE,
        })
        r = requests.get(rest_url, headers=authz_headers)
        self.assert_response(r, authz_status_code, authz_response)
        r = requests.get(rest_url)
        self.assert_response(r, authz_status_code, authz_response)
