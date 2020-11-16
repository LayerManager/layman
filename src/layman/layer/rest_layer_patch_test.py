import pytest
import importlib

from layman import settings, app
from layman.common import geoserver
from layman.layer.prime_db_schema import table as prime_db_schema
from layman.common.prime_db_schema import users

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
        gs_expected_roles = geoserver.layman_users_to_geoserver_roles(expected_roles[right_type])
        gs_roles = geoserver.get_pattern_security_roles(f'{username}.{layername}.{right_type[0]}', auth)
        assert gs_expected_roles == gs_roles\
            or ('ROLE_ANONYMOUS' in gs_expected_roles and 'ROLE_ANONYMOUS' in gs_roles), right_type


def assert_layman_layer_access_rights(username,
                                      layername,
                                      roles_to_test):
    with app.app_context():
        access_rights = prime_db_schema.get_layer_info(username, layername)['access_rights']
        if users.get_user_infos(username):
            roles_to_test['read'].add(username)
            roles_to_test['write'].add(username)
    assert set(access_rights['read']) == roles_to_test['read']
    assert set(access_rights['write']) == roles_to_test['write']


def case_test_gs_rules_inner(username,
                             layername,
                             authn_headers,
                             roles_post=None,
                             roles_patch_list=None,
                             use_file=False):
    roles_post = roles_post or {'read': f'{username}',
                                'write': f'{username}'}
    roles_patch_list = roles_patch_list or []
    roles_to_test = roles_post.copy()

    ln = client_util.publish_layer(username,
                                   layername,
                                   access_rights={key: ','.join(value) for key, value in roles_post.items()},
                                   headers=authn_headers)
    assert ln == layername
    client_util.assert_user_layers(username, [layername], authn_headers)
    assert_gs_user_and_roles(username)
    assert_gs_workspace_data_security(username)
    assert_gs_layer_data_security(username, layername, roles_to_test)
    assert_layman_layer_access_rights(username, layername, roles_to_test)

    for roles_patch in roles_patch_list:
        for right_type in ['read', 'write']:
            if roles_patch.get(right_type):
                roles_to_test[right_type] = roles_patch[right_type]
        ln = client_util.patch_layer(username,
                                     layername,
                                     access_rights={key: ','.join(value) for key, value in roles_patch.items()},
                                     headers=authn_headers,
                                     file_paths=['tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson'] if use_file else None)
        assert ln == layername
        client_util.assert_user_layers(username, [layername], authn_headers)
        assert_gs_user_and_roles(username)
        assert_gs_workspace_data_security(username)
        assert_gs_layer_data_security(username, layername, roles_to_test)
        assert_layman_layer_access_rights(username, layername, roles_to_test)

    client_util.delete_layer(username, layername, headers=authn_headers)


def case_test_gs_rules(username,
                       layername,
                       authn_headers,
                       roles_post,
                       roles_patch_list,
                       ):
    case_test_gs_rules_inner(username,
                             layername,
                             authn_headers,
                             roles_post,
                             roles_patch_list,
                             )
    case_test_gs_rules_inner(username,
                             layername,
                             authn_headers,
                             roles_post,
                             roles_patch_list,
                             True,
                             )


@pytest.mark.usefixtures('liferay_mock')
def test_access_rights():
    username = 'test_gs_rules_user'
    layername1 = 'test_gs_rules_layer'

    layman_process = process.start_layman(AUTHN_SETTINGS)
    authn_headers1 = client_util.get_authz_headers(username)

    client_util.reserve_username(username, headers=authn_headers1)
    assert_gs_user_and_roles(username)
    assert_gs_workspace_data_security(username)

    case_test_gs_rules(username,
                       layername1,
                       authn_headers1,
                       {'read': {settings.RIGHTS_EVERYONE_ROLE},
                        'write': {settings.RIGHTS_EVERYONE_ROLE}, },
                       [{'read': {settings.RIGHTS_EVERYONE_ROLE},
                         'write': {settings.RIGHTS_EVERYONE_ROLE}, }],
                       )

    case_test_gs_rules(username,
                       layername1,
                       authn_headers1,
                       {'read': {username},
                        'write': {username}, },
                       [{'read': {username},
                         'write': {username}, }],
                       )

    case_test_gs_rules(username,
                       layername1,
                       authn_headers1,
                       {'read': {settings.RIGHTS_EVERYONE_ROLE},
                        'write': {settings.RIGHTS_EVERYONE_ROLE}, },
                       [{'read': {username},
                         'write': {username}, }],
                       )

    case_test_gs_rules(username,
                       layername1,
                       authn_headers1,
                       {'read': {username},
                        'write': {username}, },
                       [{'read': {settings.RIGHTS_EVERYONE_ROLE},
                         'write': {settings.RIGHTS_EVERYONE_ROLE}, }],
                       )

    case_test_gs_rules(username,
                       layername1,
                       authn_headers1,
                       {'read': {settings.RIGHTS_EVERYONE_ROLE},
                        'write': {settings.RIGHTS_EVERYONE_ROLE}, },
                       [{'write': {username}}, ],
                       )

    case_test_gs_rules(username,
                       layername1,
                       authn_headers1,
                       {'read': {username},
                        'write': {username}, },
                       [{'read': {settings.RIGHTS_EVERYONE_ROLE}}, ],
                       )

    case_test_gs_rules(username,
                       layername1,
                       authn_headers1,
                       {'read': {username},
                        'write': {username}, },
                       [],
                       )

    process.stop_process(layman_process)
