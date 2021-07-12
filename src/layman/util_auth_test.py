import pytest

from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE
from test_tools import process_client
from . import util, app


LAYER = 'test_get_publication_info_layer'
MAP = 'test_get_publication_info_map'
USER_OWNER = 'test_get_publication_info_user'
USER_WITHOUT_RIGHTS = 'test_get_publication_info_without_user'


@pytest.fixture()
def prep_test_get_publication_info():

    auth_header_owner = process_client.get_authz_headers(USER_OWNER)
    auth_header_without = process_client.get_authz_headers(USER_WITHOUT_RIGHTS)
    process_client.ensure_reserved_username(USER_OWNER, headers=auth_header_owner)
    process_client.ensure_reserved_username(USER_WITHOUT_RIGHTS, headers=auth_header_without)

    access_rights = {'read': USER_OWNER,
                     'write': USER_OWNER}

    process_client.publish_workspace_layer(USER_OWNER, LAYER, headers=auth_header_owner, access_rights=access_rights)
    process_client.publish_workspace_map(USER_OWNER, MAP, headers=auth_header_owner, access_rights=access_rights)

    yield

    process_client.delete_workspace_map(USER_OWNER, MAP, headers=auth_header_owner)
    process_client.delete_workspace_layer(USER_OWNER, LAYER, headers=auth_header_owner)


@pytest.mark.parametrize('pub_type, pub_name, context, expected_items, not_expected_items,', [
    (LAYER_TYPE, LAYER, None, {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file'}, {}),
    (MAP_TYPE, MAP, None, {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file'}, {}),
    (LAYER_TYPE, LAYER, {'actor_name': USER_OWNER}, {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file'}, {}),
    (LAYER_TYPE, LAYER, {'actor_name': USER_WITHOUT_RIGHTS}, {}, {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file'}),
    (LAYER_TYPE, LAYER, {'actor_name': USER_OWNER, 'keys': []}, {'name', 'title', 'access_rights', 'uuid', }, {'metadata', 'file', }),
    (MAP_TYPE, MAP, {'actor_name': USER_OWNER, 'keys': []}, {'name', 'title', 'access_rights', 'uuid', }, {'metadata', 'file', }),
    (LAYER_TYPE, LAYER, {'keys': ['metadata']}, {'metadata', }, {'name', 'title', 'access_rights', 'uuid', 'file', }),
    (MAP_TYPE, MAP, {'keys': ['thumbnail']}, {'thumbnail'}, {'name', 'title', 'access_rights', 'uuid', 'file', 'metadata', }),
])
@pytest.mark.usefixtures('ensure_layman', 'liferay_mock', 'prep_test_get_publication_info')
def test_get_publication_info(pub_type,
                              pub_name,
                              context,
                              expected_items,
                              not_expected_items,
                              ):
    with app.app_context():
        pub_info = util.get_publication_info(USER_OWNER, pub_type, pub_name, context)
        for item in expected_items:
            assert item in pub_info, (item, pub_info)
        for item in not_expected_items:
            assert item not in pub_info, (item, pub_info)
