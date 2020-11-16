import pytest
import json

from layman import app, settings, LaymanError
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
            assert str(exc_info.value) == f"Authorization module is unable to authorize path {wrong_path}", exc_info.traceback


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
            with pytest.raises(Exception) as exc_info:
                mock_method()
            assert isinstance(exc_info.value, LaymanError)

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
        # ensure that raised exception is LaymanError, not Exception "Authorization module is unable to authorize path ..."
        with app.test_request_context(req_path):
            g.user = None
            with pytest.raises(Exception) as exc_info:
                mock_method()
            assert isinstance(exc_info.value, LaymanError)


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
    process_client.delete_layer(username, layername, headers=user_authz_headers)

    process.stop_process(layman_process)


def test_public_workspace_variable(liferay_mock):
    def case_test_public_workspace_variable(create_public_workspace,
                                            publish_in_public_workspace,
                                            workspace_name,
                                            layername,
                                            authz_headers,
                                            user_can_create,
                                            anonymous_can_publish,
                                            anonymous_can_create,
                                            ):
        def can_not_publish(workspace_name,
                            layername,
                            authz_headers=None,
                            ):
            r = process_client.publish_layer(workspace_name,
                                             layername,
                                             headers=authz_headers,
                                             assert_status=False)
            assert r.status_code == 403
            details = json.loads(r.text)
            assert details['code'] == 30
            assert details['message'] == "Unauthorized access"

        workspace_name2 = workspace_name + '2'
        layername2 = layername + '2'
        env_vars['GRANT_CREATE_PUBLIC_WORKSPACE'] = create_public_workspace
        env_vars['GRANT_PUBLISH_IN_PUBLIC_WORKSPACE'] = publish_in_public_workspace
        layman_process = process.start_layman(env_vars)

        if user_can_create:
            process_client.publish_layer(workspace_name, layername, headers=authz_headers)
            if anonymous_can_publish:
                process_client.publish_layer(workspace_name, layername2)
                process_client.delete_layer(workspace_name, layername2)
            process_client.delete_layer(workspace_name, layername, headers=authz_headers)
        else:
            can_not_publish(workspace_name, layername, authz_headers)

        if anonymous_can_create:
            process_client.publish_layer(workspace_name2, layername)
            process_client.delete_layer(workspace_name2, layername)
        else:
            can_not_publish(workspace_name2, layername)

        process.stop_process(layman_process)

    layername = 'test_public_workspace_variable_layer'
    username = 'test_public_workspace_variable_user'
    workspace_name = 'test_public_workspace_variable_workspace'

    user_authz_headers = process_client.get_authz_headers(username)
    env_vars = dict(process.AUTHN_SETTINGS)

    layman_process = process.start_layman(env_vars)
    process_client.reserve_username(username, headers=user_authz_headers)
    process.stop_process(layman_process)

    ############################################
    # I have to have different workspace name each time, as I tested also creation of new workspace
    case_test_public_workspace_variable('EVERYONE',
                                        'EVERYONE',
                                        workspace_name + 'ee',
                                        layername,
                                        user_authz_headers,
                                        True,
                                        True,
                                        True,
                                        )

    case_test_public_workspace_variable(username,
                                        username,
                                        workspace_name + 'uu',
                                        layername,
                                        user_authz_headers,
                                        True,
                                        False,
                                        False,
                                        )

    case_test_public_workspace_variable('',
                                        '',
                                        workspace_name + 'xx',
                                        layername,
                                        user_authz_headers,
                                        False,
                                        False,
                                        False,
                                        )

    case_test_public_workspace_variable(username,
                                        'EVERYONE',
                                        workspace_name + 'ue',
                                        layername,
                                        user_authz_headers,
                                        True,
                                        True,
                                        False,
                                        )
