import sys
import pytest
import requests

del sys.modules['layman']

from layman import app, settings
from layman import util as layman_util
from test import process_client


@pytest.mark.usefixtures('ensure_layman')
def test_get_map_title():
    username = 'test_get_map_title_user'
    maps = [("c_test_get_map_title_map", "C Test get map title - map title íářžý"),
            ("a_test_get_map_title_map", "A Test get map title - map title íářžý"),
            ("b_test_get_map_title_map", "B Test get map title - map title íářžý")
            ]
    sorted_maps = sorted(maps)

    for (name, title) in maps:
        process_client.publish_map(username, name, title=title)

    with app.app_context():
        url_get = layman_util.url_for('rest_maps.get', username=username)
    # maps.GET
    rv = requests.get(url_get)
    assert rv.status_code == 200, rv.json()

    for i in range(0, len(sorted_maps) - 1):
        assert rv.json()[i]["name"] == sorted_maps[i][0]
        assert rv.json()[i]["title"] == sorted_maps[i][1]

    for (name, title) in maps:
        process_client.delete_map(username, name)


@pytest.mark.usefixtures('ensure_layman')
def test_get_maps():
    username = 'test_get_maps_user'
    mapname = 'test_get_maps_map'

    process_client.publish_map(username, mapname, title=mapname)

    with app.app_context():
        url_get = layman_util.url_for('rest_maps.get', username=username)
    # maps.GET
    rv = requests.get(url_get)
    assert rv.status_code == 200, rv.json()

    assert rv.json()[0]['name'] == mapname
    assert rv.json()[0]['title'] == mapname
    assert rv.json()[0]['url'] == f"http://{settings.LAYMAN_SERVER_NAME}/rest/{username}/maps/{mapname}"

    process_client.delete_map(username, mapname)
