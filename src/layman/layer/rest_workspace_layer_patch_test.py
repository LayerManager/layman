import pytest

from layman import settings, app
from test_tools import geoserver_client, process_client as client_util


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

        assert_wms_access(USERNAME, owner_authn_headers, [LAYERNAME])
        assert_wms_access(USERNAME, other_authn_headers, access_rights_and_expected['expected_other_user_layers'])
        assert_wms_access(USERNAME, None, access_rights_and_expected['expected_anonymous_layers'])

    client_util.delete_workspace_layer(USERNAME, LAYERNAME, headers=owner_authn_headers)
