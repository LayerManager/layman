import pytest

from . import upgrade_v1_9
from layman import settings, app
from layman.common import geoserver as gs_common
from test import process_client
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA

auth = settings.LAYMAN_GS_AUTH


def assert_roles(workspace,
                 layer,
                 expected_roles):
    for right_type in ['read', 'write']:
        rule = f'{workspace}.{layer}.{right_type[0]}'
        roles = gs_common.get_security_roles(rule, auth)
        assert roles == expected_roles


@pytest.mark.usefixtures('ensure_layman')
def test_geoserver_everyone_rights_repair():
    workspace = 'test_geoserver_everyone_rights_repair_workspace'
    layer = 'test_geoserver_everyone_rights_repair_layer'
    expected_roles1 = {'ROLE_ANONYMOUS'}
    expected_roles2 = {'ROLE_ANONYMOUS', 'ROLE_AUTHENTICATED'}

    process_client.publish_layer(workspace, layer)
    for right_type in ['read', 'write']:
        gs_common.ensure_layer_security_roles(workspace, layer, expected_roles1, right_type[0], auth)

    assert_roles(workspace, layer, expected_roles1)

    with app.app_context():
        upgrade_v1_9.geoserver_everyone_rights_repair()

    assert_roles(workspace, layer, expected_roles2)


@pytest.mark.usefixtures('ensure_layman', 'liferay_mock')
def test_geoserver_remove_users_for_public_workspaces():
    workspace = 'test_geoserver_remove_users_for_public_workspaces_workspace'
    user = 'test_geoserver_remove_users_for_public_workspaces_user'
    auth_headers = process_client.get_authz_headers(user)
    layer = 'test_geoserver_remove_users_for_public_workspaces_layer'
    gs_rolename = gs_common.username_to_rolename(workspace)
    gs_rolename2 = gs_common.username_to_rolename(user)

    process_client.publish_layer(workspace, layer)
    process_client.ensure_reserved_username(user, auth_headers)
    with app.app_context():

        gs_common.ensure_whole_user(workspace, auth)

        usernames = gs_common.get_usernames(auth)
        assert workspace in usernames
        assert user in usernames
        roles = gs_common.get_roles(auth)
        assert gs_rolename in roles
        assert gs_rolename2 in roles
        workspaces = gs_common.get_all_workspaces(auth)
        assert workspace in workspaces
        assert user in workspaces

        upgrade_v1_9.geoserver_remove_users_for_public_workspaces()

        usernames = gs_common.get_usernames(auth)
        assert workspace not in usernames, usernames
        assert user in usernames
        roles = gs_common.get_roles(auth)
        assert gs_rolename not in roles, roles
        assert gs_rolename2 in roles
        workspaces = gs_common.get_all_workspaces(auth)
        assert workspace in workspaces, workspaces
        assert user in workspaces

    process_client.delete_layer(workspace, layer)
    process_client.publish_layer(workspace, layer)
    process_client.delete_layer(workspace, layer)
    process_client.publish_layer(workspace, layer + '2')
    process_client.delete_layer(workspace, layer + '2')
