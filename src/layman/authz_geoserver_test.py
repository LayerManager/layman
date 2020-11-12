import pytest
import importlib

from layman import settings
from layman.common import geoserver

from test import process, process_client as client_util


liferay_mock = process.liferay_mock

LIFERAY_PORT = process.LIFERAY_PORT

ISS_URL_HEADER = client_util.ISS_URL_HEADER
TOKEN_HEADER = client_util.TOKEN_HEADER

AUTHN_INTROSPECTION_URL = process.AUTHN_INTROSPECTION_URL

AUTHN_SETTINGS = process.AUTHN_SETTINGS


def assert_gs_user_and_roles(username):
    auth = settings.LAYMAN_GS_AUTH
    gs_usernames = geoserver.get_usernames(auth)
    assert username in gs_usernames
    gs_user_roles = geoserver.get_user_roles(username, auth)
    user_role = f"USER_{username.upper()}"
    assert user_role in gs_user_roles
    assert settings.LAYMAN_GS_ROLE in gs_user_roles


def assert_gs_workspace_data_security(username):
    auth = settings.LAYMAN_GS_AUTH
    user_role = f"USER_{username.upper()}"
    gs_roles = geoserver.get_workspace_security_roles(username, 'r', auth)
    assert settings.LAYMAN_GS_ROLE in gs_roles
    assert 'ROLE_ANONYMOUS' in gs_roles
    assert 'ROLE_AUTHENTICATED' in gs_roles
    gs_roles = geoserver.get_workspace_security_roles(username, 'w', auth)
    assert user_role in gs_roles


def assert_gs_layer_data_security(username,
                                  layername,
                                  expected_roles):
    auth = settings.LAYMAN_GS_AUTH
    for right_type in ['read', 'write']:
        gs_expected_roles = geoserver.layman_users_to_geoserver_roles(expected_roles[right_type].split(','))
        gs_roles = geoserver.get_pattern_security_roles(f'{username}.{layername}.{right_type[0]}', auth)
        assert gs_expected_roles == gs_roles


def case_test_gs_rules(username,
                       layername,
                       authn_headers,
                       roles_post,
                       roles_patch_list,
                       roles_patch_list_test=None):
    roles_patch_list_test = roles_patch_list_test or roles_patch_list
    ln = client_util.publish_layer(username,
                                   layername,
                                   access_rights=roles_post,
                                   headers=authn_headers)
    assert ln == layername
    client_util.assert_user_layers(username, [layername], authn_headers)
    assert_gs_user_and_roles(username)
    assert_gs_workspace_data_security(username)
    assert_gs_layer_data_security(username, layername, roles_post)

    i = 0
    for roles_patch in roles_patch_list:
        ln = client_util.patch_layer(username,
                                     layername,
                                     access_rights=roles_patch,
                                     headers=authn_headers)
        assert ln == layername
        client_util.assert_user_layers(username, [layername], authn_headers)
        assert_gs_user_and_roles(username)
        assert_gs_workspace_data_security(username)
        assert_gs_layer_data_security(username, layername, roles_patch_list_test[i])
        i = i + 1

    client_util.delete_layer(username, layername, headers=authn_headers)


def test_gs_rules(liferay_mock):
    username = 'test_gs_rules_user'
    layername1 = 'test_gs_rules_layer'

    layman_process = process.start_layman(dict(**AUTHN_SETTINGS))
    authn_headers1 = {
        f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
        f'{TOKEN_HEADER}': f'Bearer {username}',
    }
    client_util.reserve_username(username, headers=authn_headers1)
    assert_gs_user_and_roles(username)
    assert_gs_workspace_data_security(username)

    case_test_gs_rules(username,
                       layername1,
                       authn_headers1,
                       {'read': f'{settings.RIGHTS_EVERYONE_ROLE}',
                        'write': f'{settings.RIGHTS_EVERYONE_ROLE}'},
                       [{'read': f'{settings.RIGHTS_EVERYONE_ROLE}',
                         'write': f'{settings.RIGHTS_EVERYONE_ROLE}'}, ],
                       )

    case_test_gs_rules(username,
                       layername1,
                       authn_headers1,
                       {'read': f'{username}',
                        'write': f'{username}'},
                       [{'read': f'{username}',
                         'write': f'{username}'}, ],
                       )

    case_test_gs_rules(username,
                       layername1,
                       authn_headers1,
                       {'read': f'{settings.RIGHTS_EVERYONE_ROLE}',
                        'write': f'{settings.RIGHTS_EVERYONE_ROLE}'},
                       [{'read': f'{username}',
                         'write': f'{username}'}, ],
                       )

    case_test_gs_rules(username,
                       layername1,
                       authn_headers1,
                       {'read': f'{username}',
                        'write': f'{username}'},
                       [{'read': f'{settings.RIGHTS_EVERYONE_ROLE}',
                         'write': f'{settings.RIGHTS_EVERYONE_ROLE}'}, ],
                       )

    case_test_gs_rules(username,
                       layername1,
                       authn_headers1,
                       {'read': f'{settings.RIGHTS_EVERYONE_ROLE}',
                        'write': f'{settings.RIGHTS_EVERYONE_ROLE}'},
                       [{'write': f'{username}'}, ],
                       [{'read': f'{settings.RIGHTS_EVERYONE_ROLE}',
                         'write': f'{username}'}, ],
                       )

    case_test_gs_rules(username,
                       layername1,
                       authn_headers1,
                       {'read': f'{username}',
                        'write': f'{username}'},
                       [{'read': f'{settings.RIGHTS_EVERYONE_ROLE}'}, ],
                       [{'read': f'{settings.RIGHTS_EVERYONE_ROLE}',
                         'write': f'{username}'}, ],
                       )

    case_test_gs_rules(username,
                       layername1,
                       authn_headers1,
                       {'read': f'{username}',
                        'write': f'{username}'},
                       [None],
                       [{'read': f'{username}',
                         'write': f'{username}'}, ],
                       )

    process.stop_process(layman_process)
