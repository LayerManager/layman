import sys
import requests
import pytest

del sys.modules['layman']
from layman import app, settings, LaymanError
from test_tools import process_client
from test_tools.util import url_for


@pytest.mark.usefixtures('ensure_layman')
def test_get_map_title():
    workspace = 'test_get_map_title_user'
    maps = [("c_test_get_map_title_map", "C Test get map title - map title íářžý"),
            ("a_test_get_map_title_map", "A Test get map title - map title íářžý"),
            ("b_test_get_map_title_map", "B Test get map title - map title íářžý")
            ]
    sorted_maps = sorted(maps)

    map_uuids = []
    for (name, title) in maps:
        map_info = process_client.publish_workspace_map(workspace, name, title=title)
        map_uuids.append(map_info['uuid'])

    with app.app_context():
        url_get = url_for('rest_maps.get')
    # maps.GET
    response = requests.get(url_get, params={'workspace': workspace}, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    assert response.status_code == 200, response.json()

    for i in range(0, len(sorted_maps) - 1):
        assert response.json()[i]["name"] == sorted_maps[i][0]
        assert response.json()[i]["title"] == sorted_maps[i][1]

    for uuid in map_uuids:
        process_client.delete_map(uuid=uuid)


@pytest.mark.usefixtures('ensure_layman')
def test_post_maps_requires_workspace():
    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_map(
            workspace='',
            name='map_requires_workspace',
            file_paths=['sample/layman.map/small_map.json'],
        )
    assert exc_info.value.http_code == 400
    assert exc_info.value.code == 2
    assert exc_info.value.data['parameter'] == 'workspace'


@pytest.mark.usefixtures('ensure_layman')
def test_delete_maps_requires_workspace():
    with pytest.raises(LaymanError) as exc_info:
        process_client.delete_workspace_maps(workspace='')
    assert exc_info.value.http_code == 400
    assert exc_info.value.code == 2
    assert exc_info.value.data['parameter'] == 'workspace'


@pytest.mark.usefixtures('ensure_layman')
def test_get_maps_nonexistent_workspace():
    with pytest.raises(LaymanError) as exc_info:
        process_client.get_maps(workspace='workspace_that_does_not_exist_for_maps')
    assert exc_info.value.http_code == 404
    assert exc_info.value.code == 40


@pytest.mark.usefixtures('ensure_layman', 'oauth2_provider_mock')
def test_post_maps_to_foreign_personal_workspace():
    workspace_owner = 'test_owner'
    workspace_editor = 'test_not_owner'
    process_client.reserve_username(workspace_owner, actor_name=workspace_owner)
    process_client.reserve_username(workspace_editor, actor_name=workspace_editor)

    with pytest.raises(LaymanError) as exc_info:
        process_client.publish_workspace_map(
            workspace=workspace_owner,
            name='map_in_foreign_workspace',
            file_paths=['sample/layman.map/small_map.json'],
            actor_name=workspace_editor,
        )
    assert exc_info.value.http_code == 403
    assert exc_info.value.code == 30


@pytest.mark.usefixtures('ensure_layman', 'oauth2_provider_mock')
def test_get_maps_without_workspace_filters_by_read_access():
    workspace_owner = 'test_access_rights_application_owner'
    workspace_reader = 'test_access_rights_application_reader_by_username'
    process_client.reserve_username(workspace_owner, actor_name=workspace_owner)
    process_client.reserve_username(workspace_reader, actor_name=workspace_reader)

    private_map_name = 'maps_visibility_private_map'
    public_map_name = 'maps_visibility_public_map'
    private_map = process_client.publish_workspace_map(
        workspace_owner,
        private_map_name,
        file_paths=['sample/layman.map/small_map.json'],
        actor_name=workspace_owner,
        access_rights={'read': workspace_owner, 'write': workspace_owner},
    )
    public_map = process_client.publish_workspace_map(
        workspace_owner,
        public_map_name,
        file_paths=['sample/layman.map/small_map.json'],
        actor_name=workspace_owner,
        access_rights={'read': 'EVERYONE', 'write': workspace_owner},
    )

    maps_visible_to_reader = process_client.get_maps(actor_name=workspace_reader)
    visible_names = {map_info['name'] for map_info in maps_visible_to_reader}
    assert public_map_name in visible_names
    assert private_map_name not in visible_names

    process_client.delete_map(private_map['uuid'], actor_name=workspace_owner)
    process_client.delete_map(public_map['uuid'], actor_name=workspace_owner)
