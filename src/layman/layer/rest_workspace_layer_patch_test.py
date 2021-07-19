import pytest

from geoserver import util as gs_util
from layman import settings, app
from layman.layer.prime_db_schema import table as prime_db_schema
from layman.common import geoserver as gs_common
from layman.common.prime_db_schema import users
from test_tools import geoserver_client, process_client as client_util


def assert_gs_layer_data_security(username,
                                  layername,
                                  expected_roles):
    auth = settings.LAYMAN_GS_AUTH
    with app.app_context():
        is_personal_workspace = users.get_user_infos(username)
    owner_and_everyone_roles = gs_common.layman_users_to_geoserver_roles({username, settings.RIGHTS_EVERYONE_ROLE})
    owner_role_set = gs_common.layman_users_to_geoserver_roles({username})
    for right_type in ['read', 'write']:
        gs_expected_roles = gs_common.layman_users_to_geoserver_roles(expected_roles[right_type])
        gs_roles = gs_util.get_security_roles(f'{username}.{layername}.{right_type[0]}', auth)
        assert gs_expected_roles == gs_roles\
            or (is_personal_workspace
                and gs_expected_roles == owner_and_everyone_roles == gs_roles.union(owner_role_set)), right_type


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


def assert_wms_access(workspace, authn_headers, expected_layers):
    wms = geoserver_client.get_wms_capabilities(workspace, headers=authn_headers)
    assert set(wms.contents) == set(expected_layers)


USERNAME = 'test_gs_rules_user'
USERNAME2 = 'test_gs_rules_other_user'
LAYERNAME = 'test_gs_rules_layer'


@pytest.fixture(scope="module")
def ensure_user():
    # needs liferay_mock and ensure_layman fixtures
    for tmp_username in [USERNAME, USERNAME2]:
        authn_headers1 = client_util.get_authz_headers(tmp_username)

        client_util.ensure_reserved_username(tmp_username, headers=authn_headers1)


@pytest.mark.usefixtures('liferay_mock', 'ensure_layman_module', 'ensure_user')
@pytest.mark.parametrize("access_rights_and_expected_list", [
    [
        {'read': {settings.RIGHTS_EVERYONE_ROLE},
         'write': {settings.RIGHTS_EVERYONE_ROLE},
         'expected_other_user_layers': [LAYERNAME],
         'expected_anonymous_layers': [LAYERNAME], },
        {'read': {settings.RIGHTS_EVERYONE_ROLE},
         'write': {settings.RIGHTS_EVERYONE_ROLE},
         'expected_other_user_layers': [LAYERNAME],
         'expected_anonymous_layers': [LAYERNAME], },
    ], [
        {'read': {settings.RIGHTS_EVERYONE_ROLE},
         'write': {settings.RIGHTS_EVERYONE_ROLE},
         'expected_other_user_layers': [LAYERNAME],
         'expected_anonymous_layers': [LAYERNAME], },
        {'expected_other_user_layers': [LAYERNAME],
         'expected_anonymous_layers': [LAYERNAME], },
    ], [
        {'read': {USERNAME},
         'write': {USERNAME},
         'expected_other_user_layers': [],
         'expected_anonymous_layers': [], },
        {'read': {USERNAME},
         'write': {USERNAME},
         'expected_other_user_layers': [],
         'expected_anonymous_layers': [], },
    ], [
        {'read': {settings.RIGHTS_EVERYONE_ROLE},
         'write': {settings.RIGHTS_EVERYONE_ROLE},
         'expected_other_user_layers': [LAYERNAME],
         'expected_anonymous_layers': [LAYERNAME], },
        {'read': {USERNAME},
         'write': {USERNAME},
         'expected_other_user_layers': [],
         'expected_anonymous_layers': [], },
    ], [
        {'read': {USERNAME},
         'write': {USERNAME},
         'expected_other_user_layers': [],
         'expected_anonymous_layers': [], },
        {'read': {settings.RIGHTS_EVERYONE_ROLE},
         'write': {settings.RIGHTS_EVERYONE_ROLE},
         'expected_other_user_layers': [LAYERNAME],
         'expected_anonymous_layers': [LAYERNAME], },
    ], [
        {'read': {settings.RIGHTS_EVERYONE_ROLE},
         'write': {settings.RIGHTS_EVERYONE_ROLE},
         'expected_other_user_layers': [LAYERNAME],
         'expected_anonymous_layers': [LAYERNAME], },
        {'write': {USERNAME},
         'expected_other_user_layers': [LAYERNAME],
         'expected_anonymous_layers': [LAYERNAME], },
        {'read': {USERNAME},
         'expected_other_user_layers': [],
         'expected_anonymous_layers': [], },
        {'read': {USERNAME, USERNAME2},
         'expected_other_user_layers': [LAYERNAME],
         'expected_anonymous_layers': [], },
        {'read': {USERNAME, USERNAME2, settings.RIGHTS_EVERYONE_ROLE},
         'expected_other_user_layers': [LAYERNAME],
         'expected_anonymous_layers': [LAYERNAME], },
    ], [
        {'read': {USERNAME},
         'write': {USERNAME},
         'expected_other_user_layers': [],
         'expected_anonymous_layers': [], },
        {'read': {settings.RIGHTS_EVERYONE_ROLE},
         'expected_other_user_layers': [LAYERNAME],
         'expected_anonymous_layers': [LAYERNAME], },
    ], [
        {'read': {USERNAME},
         'write': {USERNAME},
         'expected_other_user_layers': [],
         'expected_anonymous_layers': [], },
    ]
])
@pytest.mark.parametrize("use_file", [False, True])
def test_access_rights(access_rights_and_expected_list, use_file):

    owner_authn_headers = client_util.get_authz_headers(USERNAME)
    other_authn_headers = client_util.get_authz_headers(USERNAME2)

    post_method = client_util.publish_workspace_layer
    patch_method = client_util.patch_workspace_layer
    full_access_rights = {
        'read': access_rights_and_expected_list[0]['read'],
        'write': access_rights_and_expected_list[0]['write'],
    }
    roles_to_test = full_access_rights.copy()
    for idx, access_rights_and_expected in enumerate(access_rights_and_expected_list):
        write_method = patch_method if idx > 0 else post_method
        access_rights = {}
        for right_type in ['read', 'write']:
            if access_rights_and_expected.get(right_type):
                roles_to_test[right_type] = access_rights_and_expected[right_type]
                access_rights[right_type] = access_rights_and_expected[right_type]
        write_method(USERNAME,
                     LAYERNAME,
                     access_rights={key: ','.join(value) for key, value in access_rights.items()},
                     headers=owner_authn_headers,
                     file_paths=[
                         'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson'
                     ] if use_file else None)

        assert_gs_layer_data_security(USERNAME, LAYERNAME, roles_to_test)
        assert_layman_layer_access_rights(USERNAME, LAYERNAME, roles_to_test)
        assert_wms_access(USERNAME, owner_authn_headers, [LAYERNAME])
        assert_wms_access(USERNAME, other_authn_headers, access_rights_and_expected['expected_other_user_layers'])
        assert_wms_access(USERNAME, None, access_rights_and_expected['expected_anonymous_layers'])

    client_util.delete_workspace_layer(USERNAME, LAYERNAME, headers=owner_authn_headers)
