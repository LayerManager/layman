import pytest
from layman import app, util as layman_util, settings
from layman.layer.filesystem import gdal, thumbnail as layer_thumbnail
from layman.map.filesystem import thumbnail as map_thumbnail
from test_tools import assert_util, util as test_util, process_client
from .. import util
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

    all_auth_info = util.get_users_and_headers_for_publication(workspace, publ_type, publication)
    headers_list_in = all_auth_info['read'][util.KEY_AUTH][util.KEY_HEADERS]
    headers_list_out = all_auth_info['read'][util.KEY_NOT_AUTH][util.KEY_HEADERS]

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

    all_auth_info = util.get_users_and_headers_for_publication(workspace, publ_type, publication)
    readers = all_auth_info['read'][util.KEY_AUTH][util.KEY_USERS]
    non_readers = all_auth_info['read'][util.KEY_NOT_AUTH][util.KEY_USERS]

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
    assert {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file', }.issubset(set(pub_info)), pub_info

    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, publication, {'keys': ['metadata']})
    assert {'metadata', }.issubset(set(pub_info)), pub_info
    assert all(item not in pub_info for item in {'name', 'title', 'access_rights', 'uuid', 'file', }), pub_info

    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, publication, {'keys': ['thumbnail']})
    assert {'thumbnail', }.issubset(set(pub_info)), pub_info
    assert all(item not in pub_info for item in {'name', 'title', 'access_rights', 'uuid', 'file', 'metadata', }), pub_info

    user = workspace if is_personal_workspace else settings.ANONYM_USER
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, publication, {'actor_name': user, 'keys': []})
    assert {'name', 'title', 'access_rights', 'uuid', }.issubset(set(pub_info)), pub_info
    assert all(item not in pub_info for item in {'metadata', 'file', }), pub_info

    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, publication, {'actor_name': user})
    assert {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file', }.issubset(set(pub_info)), pub_info


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_info(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    headers = data.HEADERS.get(workspace)
    with app.app_context():
        info = process_client.get_workspace_publication(publ_type, workspace, publication, headers)

    # Items
    assert {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file'}.issubset(set(info)), info

    # Access rights
    all_auth_info = util.get_users_and_headers_for_publication(workspace, publ_type, publication)
    for right in ['read', 'write']:
        exp_list = all_auth_info[right][util.KEY_AUTH][util.KEY_EXP_LIST]
        assert set(exp_list) == set(info['access_rights'][right])

    # Bounding box
    exp_bbox = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('bbox')
    if exp_bbox:
        info_bbox = info['bounding_box']
        assert_util.assert_same_bboxes(info_bbox, exp_bbox, 0.01)

        file_type = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('file_type')
        if file_type == settings.FILE_TYPE_RASTER:
            bbox = gdal.get_bbox(workspace, publication)
            assert_util.assert_same_bboxes(bbox, exp_bbox, 0.01)
