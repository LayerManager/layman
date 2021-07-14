import pytest
from layman import app, util as layman_util, settings
from layman.layer.filesystem import gdal, thumbnail as layer_thumbnail
from layman.map.filesystem import thumbnail as map_thumbnail
from test_tools import assert_util, util as test_util, process_client
from ... import single_static_publication as data
from ..data import ensure_publication


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_ALL_PUBLICATIONS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_bbox(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    with app.app_context():
        info = layman_util.get_publication_info(workspace, publ_type, publication, context={'keys': ['bounding_box']})

    exp_bbox = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('bbox')
    if exp_bbox:
        info_bbox = info['bounding_box']
        assert_util.assert_same_bboxes(info_bbox, exp_bbox, 0.01)

        file_type = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('file_type')
        if file_type == settings.FILE_TYPE_RASTER:
            bbox = gdal.get_bbox(workspace, publication)
            assert_util.assert_same_bboxes(bbox, exp_bbox, 0.01)


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
    is_private = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('private')

    all_sources = []
    for type_def in layman_util.get_publication_types(use_cache=False).values():
        all_sources += type_def['internal_sources']
    providers = layman_util.get_providers_from_source_names(all_sources)
    for provider in providers:
        with app.app_context():
            usernames = provider.get_usernames()
        if not is_private:
            assert workspace not in usernames, (publ_type, provider)

    with app.app_context():
        usernames = layman_util.get_usernames(use_cache=False)
        workspaces = layman_util.get_workspaces(use_cache=False)

    if is_private:
        assert workspace in usernames
    else:
        assert workspace not in usernames
    assert workspace in workspaces


@pytest.mark.parametrize('context, expected_publications', [
    ({'actor_name': 'test_get_publication_infos_user_actor', 'access_type': 'read'}, {'post_public_sld', 'post_private_write_sld'},),
    ({'actor_name': 'test_get_publication_infos_user_actor', 'access_type': 'write'}, {'post_public_sld'},),
], )
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman',)
def test_get_publication_infos(context,
                               expected_publications):
    ensure_publication(data.OWNER, process_client.LAYER_TYPE, 'post_private_sld')
    ensure_publication(data.OWNER, process_client.LAYER_TYPE, 'post_private_write_sld')
    ensure_publication(data.OWNER, process_client.LAYER_TYPE, 'post_public_sld')

    with app.app_context():
        infos = layman_util.get_publication_infos(data.OWNER, process_client.LAYER_TYPE, context)
    publ_set = set(publication_name for (workspace, publication_type, publication_name) in infos.keys())
    assert expected_publications.issubset(publ_set), publ_set
