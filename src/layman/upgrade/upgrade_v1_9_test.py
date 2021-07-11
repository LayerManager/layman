from test_tools import process_client
import pytest

from geoserver import util as gs_util
from layman import settings, app
from layman.layer import geoserver as gs_provider
from . import upgrade_v1_9
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA

auth = settings.LAYMAN_GS_AUTH


def assert_roles(workspace,
                 layer,
                 expected_roles):
    for right_type in ['read', 'write']:
        rule = f'{workspace}.{layer}.{right_type[0]}'
        roles = gs_util.get_security_roles(rule, auth)
        assert roles == expected_roles


@pytest.mark.usefixtures('ensure_layman')
def test_geoserver_everyone_rights_repair():
    workspace = 'test_geoserver_everyone_rights_repair_workspace'
    layer = 'test_geoserver_everyone_rights_repair_layer'
    expected_roles1 = {'ROLE_ANONYMOUS'}
    expected_roles2 = {'ROLE_ANONYMOUS', 'ROLE_AUTHENTICATED'}

    process_client.publish_workspace_layer(workspace, layer)
    for right_type in ['read', 'write']:
        gs_util.ensure_layer_security_roles(workspace, layer, expected_roles1, right_type[0], auth)

    assert_roles(workspace, layer, expected_roles1)

    with app.app_context():
        upgrade_v1_9.geoserver_everyone_rights_repair()

    assert_roles(workspace, layer, expected_roles2)
    process_client.delete_workspace_layer(workspace, layer)


@pytest.mark.usefixtures('ensure_layman', 'liferay_mock')
def test_geoserver_remove_users_for_public_workspaces():
    workspace = 'test_geoserver_remove_users_for_public_workspaces_workspace'
    user = 'test_geoserver_remove_users_for_public_workspaces_user'
    auth_headers = process_client.get_authz_headers(user)
    layer = 'test_geoserver_remove_users_for_public_workspaces_layer'
    gs_rolename = gs_util.username_to_rolename(workspace)
    gs_rolename2 = gs_util.username_to_rolename(user)

    process_client.publish_workspace_layer(workspace, layer)
    process_client.ensure_reserved_username(user, auth_headers)
    with app.app_context():

        gs_provider.ensure_whole_user(workspace, auth)

        usernames = gs_util.get_usernames(auth)
        assert workspace in usernames
        assert user in usernames
        roles = gs_util.get_roles(auth)
        assert gs_rolename in roles
        assert gs_rolename2 in roles
        workspaces = gs_util.get_all_workspaces(auth)
        assert workspace in workspaces
        assert user in workspaces

        upgrade_v1_9.geoserver_remove_users_for_public_workspaces()

        usernames = gs_util.get_usernames(auth)
        assert workspace not in usernames, usernames
        assert user in usernames
        roles = gs_util.get_roles(auth)
        assert gs_rolename not in roles, roles
        assert gs_rolename2 in roles
        workspaces = gs_util.get_all_workspaces(auth)
        assert workspace in workspaces, workspaces
        assert user in workspaces

    process_client.delete_workspace_layer(workspace, layer)
    process_client.publish_workspace_layer(workspace, layer)
    process_client.delete_workspace_layer(workspace, layer)
    process_client.publish_workspace_layer(workspace, layer + '2')
    process_client.delete_workspace_layer(workspace, layer + '2')
