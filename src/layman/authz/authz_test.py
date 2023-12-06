from flask import g
import pytest

from layman import app, settings, LaymanError
from . import authorize_workspace_publications_decorator, split_user_and_role_names


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


@pytest.mark.parametrize('roles_and_users, exp_users, exp_roles', [
    pytest.param([], [], [], id='no-names'),
    pytest.param(['user1', 'user2'], ['user1', 'user2'], [], id='only-users'),
    pytest.param(['ROLE1', 'EVERYONE'], [], ['ROLE1', 'EVERYONE'], id='only-roles'),
    pytest.param(['ROLE2', 'user1', 'EVERYONE', 'user2'], ['user1', 'user2'], ['ROLE2', 'EVERYONE'],
                 id='more-users-and-roles'),
])
def test_split_user_and_role_names(roles_and_users, exp_users, exp_roles):
    user_names, role_names = split_user_and_role_names(roles_and_users)
    assert user_names == exp_users
    assert role_names == exp_roles
