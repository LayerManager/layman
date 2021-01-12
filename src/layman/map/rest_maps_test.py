import sys
import pytest
import requests

del sys.modules['layman']

from layman import app, settings
from .filesystem import uuid
from . import MAP_TYPE
from layman import util as layman_util
from test import process_client, util as test_util


@pytest.mark.usefixtures('ensure_layman')
def test_get_publication_infos():
    username = 'test_get_publication_infos_user'
    mapname = 'test_get_publication_infos_layer'
    maptitle = "Test get publication infos - publication title íářžý"

    process_client.publish_map(username, mapname, title=maptitle)

    with app.app_context():
        result_infos_all = {(username, MAP_TYPE, mapname): {'name': mapname,
                                                            'title': maptitle,
                                                            'uuid': uuid.get_map_uuid(username, mapname),
                                                            'type': MAP_TYPE,
                                                            'access_rights': {'read': [settings.RIGHTS_EVERYONE_ROLE, ],
                                                                              'write': [settings.RIGHTS_EVERYONE_ROLE, ],
                                                                              }
                                                            }}
        map_infos = layman_util.get_publication_infos(username, MAP_TYPE)
        test_util.assert_same_infos(map_infos, result_infos_all, 'layman_util.get_publication_infos')

    process_client.delete_map(username, mapname)


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
