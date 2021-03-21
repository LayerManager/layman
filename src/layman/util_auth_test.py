from test import process_client
import pytest

from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE
from . import util, app


layer = 'test_get_publication_info_layer'
map = 'test_get_publication_info_map'
user_owner = 'test_get_publication_info_user'
user_without_rights = 'test_get_publication_info_without_user'


@pytest.fixture()
def prep_test_get_publication_info():

    auth_header_owner = process_client.get_authz_headers(user_owner)
    auth_header_without = process_client.get_authz_headers(user_without_rights)
    process_client.ensure_reserved_username(user_owner, headers=auth_header_owner)
    process_client.ensure_reserved_username(user_without_rights, headers=auth_header_without)

    access_rights = {'read': user_owner,
                     'write': user_owner}

    process_client.publish_workspace_layer(user_owner, layer, headers=auth_header_owner, access_rights=access_rights)
    process_client.publish_workspace_map(user_owner, map, headers=auth_header_owner, access_rights=access_rights)

    yield

    process_client.delete_workspace_map(user_owner, map, headers=auth_header_owner)
    process_client.delete_workspace_layer(user_owner, layer, headers=auth_header_owner)


@pytest.mark.parametrize('pub_type, pub_name, context, expected_items, not_expected_items,', [
    (LAYER_TYPE, layer, None, {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file'}, {}),
    (MAP_TYPE, map, None, {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file'}, {}),
    (LAYER_TYPE, layer, {'actor_name': user_owner}, {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file'}, {}),
    (LAYER_TYPE, layer, {'actor_name': user_without_rights}, {}, {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file'}),
    (LAYER_TYPE, layer, {'actor_name': user_owner, 'keys': []}, {'name', 'title', 'access_rights', 'uuid', }, {'metadata', 'file', }),
    (MAP_TYPE, map, {'actor_name': user_owner, 'keys': []}, {'name', 'title', 'access_rights', 'uuid', }, {'metadata', 'file', }),
    (LAYER_TYPE, layer, {'keys': ['metadata']}, {'metadata', }, {'name', 'title', 'access_rights', 'uuid', 'file', }),
    (MAP_TYPE, map, {'keys': ['thumbnail']}, {'thumbnail'}, {'name', 'title', 'access_rights', 'uuid', 'file', 'metadata', }),
])
@pytest.mark.usefixtures('ensure_layman', 'liferay_mock', 'prep_test_get_publication_info')
def test_get_publication_info(pub_type,
                              pub_name,
                              context,
                              expected_items,
                              not_expected_items,
                              ):
    with app.app_context():
        pub_info = util.get_publication_info(user_owner, pub_type, pub_name, context)
        for item in expected_items:
            assert item in pub_info, (item, pub_info)
        for item in not_expected_items:
            assert item not in pub_info, (item, pub_info)
