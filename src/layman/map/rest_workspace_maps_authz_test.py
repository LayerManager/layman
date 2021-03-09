import json
import pytest
from test import process_client


def assert_operates_on(workspace, mapname, expected_layers, authz_headers):
    md_comparison = process_client.get_map_metadata_comparison(workspace, mapname, authz_headers)
    operates_on = md_comparison['metadata_properties']['operates_on']
    assert (operates_on['equal']), json.dumps(operates_on, indent=2)
    assert (operates_on['equal_or_null']), json.dumps(operates_on, indent=2)
    assert (len(operates_on['values'].values()) == 2)  # GET Map File, CSW
    for operates_on_value in operates_on['values'].values():
        for (layer_uuid, layer_title) in expected_layers:
            layer_record = next(rec for rec in operates_on_value
                                if rec['xlink:title'] == layer_title and layer_uuid in rec['xlink:href'])
            assert layer_record, f"Layer uuid={layer_uuid}, title={layer_title} not found in operates_on value {json.dumps(operates_on_value, indent=2)}"
        assert len(expected_layers) == len(
            operates_on_value), f"Expected layers {expected_layers}, found {json.dumps(operates_on_value, indent=2)}"


@pytest.mark.usefixtures('ensure_layman', 'liferay_mock')
def test_map_with_unauthorized_layer():
    username1 = 'test_map_with_unauthorized_layer_user1'
    layername1 = 'test_map_with_unauthorized_layer_layer1'
    mapname1 = 'test_map_with_unauthorized_layer_map1'
    username2 = 'test_map_with_unauthorized_layer_user2'
    layername2 = 'test_map_with_unauthorized_layer_layer2'

    user1_authz_headers = process_client.get_authz_headers(username1)
    user2_authz_headers = process_client.get_authz_headers(username2)

    process_client.reserve_username(username1, headers=user1_authz_headers)
    process_client.reserve_username(username2, headers=user2_authz_headers)

    process_client.publish_layer(username1, layername1, headers=user1_authz_headers)
    process_client.publish_layer(username2, layername2, headers=user2_authz_headers)

    # assert users have access only to their own layer
    process_client.assert_user_layers(username1, [layername1], headers=user1_authz_headers)
    process_client.assert_user_layers(username1, [], headers=user2_authz_headers)
    process_client.assert_user_layers(username2, [layername2], headers=user2_authz_headers)
    process_client.assert_user_layers(username2, [], headers=user1_authz_headers)

    # publish map composed of layers of both users, read for everyone
    process_client.publish_map(
        username1,
        mapname1,
        file_paths=['sample/layman.map/internal_url_unauthorized_layer.json'],
        access_rights={
            'read': 'EVERYONE',
            'write': f"{username1},{username2}",
        },
        headers=user1_authz_headers,
    )
    process_client.assert_user_maps(username1, [mapname1], headers=user1_authz_headers)
    process_client.assert_user_maps(username1, [mapname1], headers=user2_authz_headers)

    layer1_uuid = process_client.get_layer(username1, layername1, headers=user1_authz_headers)['uuid']
    layer2_uuid = process_client.get_layer(username2, layername2, headers=user2_authz_headers)['uuid']

    # assert that metadata property operates_on contains only layers visible to publisher, whoever is asking and has read access to the map
    assert_operates_on(username1, mapname1, [(layer1_uuid, layername1)], authz_headers=user1_authz_headers)
    assert_operates_on(username1, mapname1, [(layer1_uuid, layername1)], authz_headers=user2_authz_headers)

    process_client.patch_map(username1, mapname1, headers=user2_authz_headers)

    # assert that metadata property operates_on contains only layers visible to last publisher, whoever is asking and has read access to the map
    assert_operates_on(username1, mapname1, [(layer2_uuid, layername2)], authz_headers=user1_authz_headers)
    assert_operates_on(username1, mapname1, [(layer2_uuid, layername2)], authz_headers=user2_authz_headers)

    # clean up
    process_client.delete_map(username1, mapname1, headers=user1_authz_headers)
    process_client.delete_layer(username1, layername1, headers=user1_authz_headers)
    process_client.delete_layer(username2, layername2, headers=user2_authz_headers)
