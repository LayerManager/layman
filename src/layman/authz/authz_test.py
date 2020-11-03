import pytest
from layman import app, settings
from flask import g
from . import authorize_decorator, parse_request_path, MULTI_PUBLICATION_PATH_PATTERN, SINGLE_PUBLICATION_PATH_PATTERN
from test import process, process_client


liferay_mock = process.liferay_mock


def test_authorize_assert_wrong_path():
    wrong_paths = [
        '/rest/layers',
        '/rest/layers/abc',
        '/rest/username/abc',
        '/rest/username/publications',
        '/rest/username/publications/blablabla',
        '/rest/username/publications/blablabla/da',
        '/rest/users/layers',
        '/rest/users/maps/map',
    ]

    @authorize_decorator
    def mock_method():
        pass

    for wrong_path in wrong_paths:
        (workspace, publication_type, publication_name) = parse_request_path(wrong_path)
        assert not workspace or not publication_type, f"Parsing {wrong_path} returns {(workspace, publication_type, publication_name)}"
        with app.test_request_context(wrong_path):
            with pytest.raises(Exception) as exc_info:
                mock_method()
            assert str(exc_info.value) == f"Authorization module is unable to authorize path {wrong_path}"


def test_authorize_accepts_path():

    @authorize_decorator
    def mock_method():
        pass

    multi_paths = [
        '/rest/user_a/layers',
        '/rest/user_a/layers/',
        '/rest/user_a/maps/',
    ]
    for req_path in multi_paths:
        m = MULTI_PUBLICATION_PATH_PATTERN.match(req_path)
        assert m, {req_path}
        (workspace, publication_type, publication_name) = parse_request_path(req_path)
        assert workspace and publication_type and not publication_name, f"Parsing {req_path} returns {(workspace, publication_type, publication_name)}"
        with app.test_request_context(req_path):
            g.user = None
            mock_method()

    single_paths = [
        '/rest/user_a/layers/abc',
        '/rest/user_a/layers/some_layer/some/nested/endpoint',
        '/rest/user_a/maps/a_map',
    ]
    for req_path in single_paths:
        m = SINGLE_PUBLICATION_PATH_PATTERN.match(req_path)
        assert m, f"{req_path} {SINGLE_PUBLICATION_PATH_PATTERN}"
        (workspace, publication_type, publication_name) = parse_request_path(req_path)
        assert workspace and publication_type and publication_name, f"Parsing {req_path} returns {(workspace, publication_type, publication_name)}"
        with app.test_request_context(req_path):
            g.user = None
            mock_method()


def test_authorize_decorator(liferay_mock):
    layername = 'test_authorize_decorator_layer'
    username = 'test_authorize_decorator_user'

    layman_process = process.start_layman(process.AUTHN_SETTINGS)

    user_authz_headers = process_client.get_authz_headers(username)

    process_client.reserve_username(username, headers=user_authz_headers)

    process_client.publish_layer(username, layername, headers=user_authz_headers)
    process_client.assert_user_layers(username, [layername], headers=user_authz_headers)
    process_client.assert_user_layers(username, [])

    process_client.patch_layer(username, layername, headers=user_authz_headers, access_rights={
        'read': settings.RIGHTS_EVERYONE_ROLE,
    })
    process_client.assert_user_layers(username, [layername], headers=user_authz_headers)
    process_client.assert_user_layers(username, [layername])

    process.stop_process(layman_process)
