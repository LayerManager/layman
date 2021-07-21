import pytest
from layman import app, util as layman_util, settings
from layman.layer.filesystem import gdal, thumbnail as layer_thumbnail
from layman.map.filesystem import thumbnail as map_thumbnail
from test_tools import assert_util, util as test_util, process_client
from ... import static_publications as data
from ..data import ensure_publication


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_thumbnail(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    thumbnail_path_method = {process_client.LAYER_TYPE: layer_thumbnail.get_layer_thumbnail_path,
                             process_client.MAP_TYPE: map_thumbnail.get_map_thumbnail_path}

    exp_thumbnail = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('thumbnail')
    if exp_thumbnail:
        with app.app_context():
            thumbnail_path = thumbnail_path_method[publ_type](workspace, publication)
        diffs = test_util.compare_images(exp_thumbnail, thumbnail_path)
        assert diffs < 1000


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_user_workspace(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    is_private_workspace = workspace in data.USERS

    all_sources = []
    for type_def in layman_util.get_publication_types(use_cache=False).values():
        all_sources += type_def['internal_sources']
    providers = layman_util.get_providers_from_source_names(all_sources)
    for provider in providers:
        with app.app_context():
            usernames = provider.get_usernames()
        if not is_private_workspace:
            assert workspace not in usernames, (publ_type, provider)

    with app.app_context():
        usernames = layman_util.get_usernames(use_cache=False)
        workspaces = layman_util.get_workspaces(use_cache=False)

    if is_private_workspace:
        assert workspace in usernames
    else:
        assert workspace not in usernames
    assert workspace in workspaces


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman',)
def test_get_publication_info_items(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    with app.app_context():
        all_items = layman_util.get_publication_types()[publ_type]['internal_sources'].values()
        for source_def in all_items:
            for key in source_def.info_items:
                context = {'keys': [key]}
                info = layman_util.get_publication_info(workspace, publ_type, publication, context)
                assert key in info or not info, info

                all_sibling_keys = set(sibling_key for item_list in all_items for sibling_key in item_list.info_items
                                       if key in item_list.info_items)
                internal_keys = [key[1:] for key in info if key.startswith('_')]
                assert set(internal_keys) <= all_sibling_keys,\
                    f'internal_keys={set(internal_keys)}, all_sibling_keys={all_sibling_keys}, key={key}, info={info}'


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_infos(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    title = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('title') or publication
    headers = data.HEADERS.get(workspace)
    infos = process_client.get_workspace_publications(publ_type, workspace, headers=headers)

    publication_infos = [info for info in infos if info['name'] == publication]
    assert len(publication_infos) == 1, f'publication_infos={publication_infos}'

    info = next(iter(publication_infos))
    assert info['title'] == title, f'publication_infos={publication_infos}'

    get_workspace_publication_url = process_client.PUBLICATION_TYPES_DEF[publ_type].get_workspace_publication_url
    param_name = process_client.PUBLICATION_TYPES_DEF[publ_type].url_param_name
    with app.app_context():
        expected_url = test_util.url_for(get_workspace_publication_url, workspace=workspace, **{param_name: publication},
                                         internal=False)
        assert info['url'] == expected_url, f'publication_infos={publication_infos}, expected_url={expected_url}'


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_auth_get_publications(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    users_can_read = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('users_can_read')
    if users_can_read:
        headers_list_in = [header for user, header in data.HEADERS.items() if user in users_can_read]
        headers_list_out = [header for user, header in data.HEADERS.items() if user not in users_can_read] + [None]
    else:
        headers_list_in = list(data.HEADERS.values()) + [None]
        headers_list_out = []

    for in_headers in headers_list_in:
        infos = process_client.get_workspace_publications(publ_type, workspace, headers=in_headers)
        publication_names = [li['name'] for li in infos]
        assert publication in publication_names, in_headers

    for out_headers in headers_list_out:
        infos = process_client.get_workspace_publications(publ_type, workspace, headers=out_headers)
        publication_names = [li['name'] for li in infos]
        assert publication not in publication_names, out_headers


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_auth_get_publication(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    users_can_read = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('users_can_read')
    users = data.USERS | {settings.ANONYM_USER, settings.NONAME_USER}
    if users_can_read:
        readers = users_can_read
        non_readers = {item for item in users if item not in users_can_read}
    else:
        readers = users
        non_readers = set()

    for user in readers:
        with app.app_context():
            pub_info = layman_util.get_publication_info(workspace, publ_type, publication, {'actor_name': user})
        assert pub_info['name'] == publication, f'pub_info={pub_info}'
        assert pub_info['type'] == publ_type, f'pub_info={pub_info}'

    for user in non_readers:
        with app.app_context():
            pub_info = layman_util.get_publication_info(workspace, publ_type, publication, {'actor_name': user})
        assert pub_info == dict(), pub_info


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_internal_info(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    is_personal_workspace = workspace in data.USERS
    # Items
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, publication)
    for item in {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file'}:
        assert item in pub_info, (item, pub_info)

    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, publication, {'keys': ['metadata']})
    for item in {'metadata', }:
        assert item in pub_info, (item, pub_info)
    for item in {'name', 'title', 'access_rights', 'uuid', 'file', }:
        assert item not in pub_info, (item, pub_info)

    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, publication, {'keys': ['thumbnail']})
    for item in {'thumbnail'}:
        assert item in pub_info, (item, pub_info)
    for item in {'name', 'title', 'access_rights', 'uuid', 'file', 'metadata', }:
        assert item not in pub_info, (item, pub_info)

    user = workspace if is_personal_workspace else settings.ANONYM_USER
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, publication, {'actor_name': user, 'keys': []})
    for item in {'name', 'title', 'access_rights', 'uuid', }:
        assert item in pub_info, (item, pub_info)
    for item in {'metadata', 'file', }:
        assert item not in pub_info, (item, pub_info)

    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, publication, {'actor_name': user})
    for item in {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file'}:
        assert item in pub_info, (item, pub_info)


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_info(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    is_personal_workspace = workspace in data.USERS
    headers = data.HEADERS.get(workspace)
    with app.app_context():
        info = process_client.get_workspace_publication(publ_type, workspace, publication, headers)

    # Items
    for item in {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file'}:
        assert item in info, (item, info)

    # Access rights
    for right in ['read', 'write']:
        users_can = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('users_can_' + right)
        if not users_can:
            users_can = {settings.RIGHTS_EVERYONE_ROLE}
            if is_personal_workspace:
                users_can.add(workspace)

        assert set(users_can) == set(info['access_rights'][right])

    # Bounding box
    exp_bbox = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('bbox')
    if exp_bbox:
        info_bbox = info['bounding_box']
        assert_util.assert_same_bboxes(info_bbox, exp_bbox, 0.01)

        file_type = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('file_type')
        if file_type == settings.FILE_TYPE_RASTER:
            bbox = gdal.get_bbox(workspace, publication)
            assert_util.assert_same_bboxes(bbox, exp_bbox, 0.01)
