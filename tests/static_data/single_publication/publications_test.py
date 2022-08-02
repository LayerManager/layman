import pytest

import crs as crs_def
from layman import app, util as layman_util, settings
from layman.common import bbox as bbox_util
from layman.layer.filesystem import gdal
from test_tools import assert_util, process_client
from .. import util
from ... import static_data as data
from ...asserts.final.publication import internal as asserts_internal, rest as asserts_rest, internal_rest as asserts_internal_rest
from ..data import ensure_publication


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_thumbnail(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    exp_thumbnail = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('thumbnail')
    if exp_thumbnail:
        asserts_internal.thumbnail_equals(workspace, publ_type, publication, exp_thumbnail)


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman',)
def test_get_publication_info_items(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    asserts_internal.source_has_its_key_or_it_is_empty(workspace, publ_type, publication)


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_infos(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    publ_def = data.PUBLICATIONS[(workspace, publ_type, publication)]
    headers = data.HEADERS.get(publ_def[data.TEST_DATA].get('users_can_write', [None])[0])
    asserts_internal_rest.same_title_in_source_and_rest_multi(workspace, publ_type, publication, headers)
    asserts_rest.is_in_rest_multi(workspace, publ_type, publication, headers)
    asserts_rest.correct_url_in_rest_multi(workspace, publ_type, publication, headers)
    if 'file_type' in publ_def[data.TEST_DATA]:
        exp_file_type = publ_def[data.TEST_DATA]['file_type']
        asserts_rest.correct_file_type_in_rest_multi(workspace, publ_type, publication, headers, exp_file_type)


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
    asserts_internal.mandatory_keys_in_all_sources(workspace, publ_type, publication)
    asserts_internal.metadata_key_sources_do_not_contain_other_keys(workspace, publ_type, publication)
    asserts_internal.metadata_key_sources_do_not_contain_other_keys(workspace, publ_type, publication)
    asserts_internal.thumbnail_key_sources_do_not_contain_other_keys(workspace, publ_type, publication)
    actor = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('users_can_write', [None])[0]
    asserts_internal.mandatory_keys_in_primary_db_schema_of_actor(workspace, publ_type, publication, actor)
    asserts_internal.other_keys_not_in_primary_db_schema_of_actor(workspace, publ_type, publication, actor)


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_info(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    headers = data.HEADERS.get(data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('users_can_write', [None])[0])
    with app.app_context():
        info = process_client.get_workspace_publication(publ_type, workspace, publication, headers)

    asserts_rest.is_complete_in_rest(info)
    asserts_rest.mandatory_keys_in_rest(info)

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
            native_bbox = gdal.get_bbox(workspace, publication)
            with app.app_context():
                bbox_3857 = bbox_util.transform(native_bbox, info['native_crs'], crs_def.EPSG_3857)
            assert_util.assert_same_bboxes(bbox_3857, exp_bbox, 0.01)


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_all_source_info(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    asserts_internal.same_value_of_key_in_all_sources(workspace, publ_type, publication)
