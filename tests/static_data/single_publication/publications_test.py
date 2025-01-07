import pytest

import crs as crs_def
from layman import app, settings
from layman.common import bbox as bbox_util
from layman.layer.filesystem import gdal
from test_tools import assert_util, process_client
from .. import util
from ... import static_data as data
from ...asserts.final.publication import internal as asserts_internal, rest as asserts_rest
from ..data import ensure_publication


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman')
def test_thumbnail(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    publ_data = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA]
    exp_thumbnail = publ_data.get('thumbnail')
    if exp_thumbnail:
        asserts_internal.thumbnail_equals(workspace, publ_type, publication, exp_thumbnail,
                                          max_diffs=publ_data.get('max_pixel_diffs'))


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman',)
def test_get_publication_info_items(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    asserts_internal.source_has_its_key_or_it_is_empty(workspace, publ_type, publication)
    asserts_internal.source_internal_keys_are_subset_of_source_sibling_keys(workspace, publ_type, publication)
    asserts_internal.all_keys_assigned_to_source(workspace, publ_type, publication)


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman')
def test_infos(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    publ_def = data.PUBLICATIONS[(workspace, publ_type, publication)]
    headers = data.HEADERS.get(publ_def[data.TEST_DATA].get('users_can_write', [None])[0])
    rest_detail = process_client.get_workspace_publication(publ_type, workspace, publication, headers=headers)
    asserts_rest.same_values_in_detail_and_multi(workspace, publ_type, publication, rest_detail, headers)
    if 'geodata_type' in publ_def[data.TEST_DATA]:
        exp_geodata_type = publ_def[data.TEST_DATA]['geodata_type']
        assert rest_detail['geodata_type'] == exp_geodata_type


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman')
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
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman')
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

        geodata_type = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('geodata_type')
        if geodata_type == settings.GEODATA_TYPE_RASTER:
            native_bbox = gdal.get_bbox(workspace, publication)
            with app.app_context():
                bbox_3857 = bbox_util.transform(native_bbox, info['native_crs'], crs_def.EPSG_3857)
            assert_util.assert_same_bboxes(bbox_3857, exp_bbox, 0.01)


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman')
def test_all_source_info(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    asserts_internal.same_value_of_key_in_all_sources(workspace, publ_type, publication)
