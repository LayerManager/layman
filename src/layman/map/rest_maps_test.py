import sys

del sys.modules['layman']

from layman import app
from .filesystem import input_file, uuid, thumbnail
from .micka import soap
from . import util
from layman.util import url_for
from test import flask_client as client_util

client = client_util.client


def test_get_map_infos(client):
    username = 'test_get_map_infos_user'
    mapname = 'test_get_map_infos_layer'
    maptitle = "Test get map infos - map title íářžý"

    client_util.publish_map(username, mapname, client, maptitle)

    result_infos_name = {mapname: {'name': mapname}}
    result_infos_name_title = {mapname: {'name': mapname, 'title': maptitle}}
    result_publication_name = [mapname]

    with app.app_context():
        result_infos_all = {mapname: {'name': mapname,
                                      'title': maptitle,
                                      'uuid': uuid.get_map_uuid(username, mapname)}}
        modules = [
            {'name': 'filesystem.input_file',
             'method_infos': input_file.get_map_infos,
             'result_infos': result_infos_name_title,
             'method_publications': input_file.get_publication_names,
             'result_publications': result_publication_name},
            {'name': 'filesystem.uuid',
             'method_infos': uuid.get_map_infos,
             'result_infos': result_infos_all,
             'method_publications': uuid.get_publication_names,
             'result_publications': result_publication_name},
            {'name': 'filesystem.thumbnail',
             'method_infos': thumbnail.get_map_infos,
             'result_infos': result_infos_name_title,
             'method_publications': thumbnail.get_publication_names,
             'result_publications': result_publication_name},
            {'name': 'micka.soap',
             'method_infos': soap.get_map_infos,
             'result_infos': {},
             'method_publications': soap.get_publication_names,
             'result_publications': []}
        ]

        for module in modules:
            map_infos = module["method_infos"](username)
            assert map_infos == module["result_infos"],\
                   (module["name"], module["method_infos"].__module__, map_infos)
            publication_names = module["method_publications"](username, "layman.map")
            assert publication_names == module["result_publications"],\
                   (module["name"], module["method_publications"].__module__, publication_names)

        map_infos = util.get_map_infos(username)
        assert map_infos == result_infos_all, map_infos

    client_util.delete_map(username, mapname, client)


def test_get_map(client):
    username = 'test_get_map_infos_user'
    mapname = 'test_get_map_infos_layer'
    maptitle = "Test get map infos - map title íářžý"

    client_util.publish_map(username, mapname, client, maptitle)

    with app.app_context():
        # maps.GET
        rv = client.get(url_for('rest_maps.get', username=username))
        assert rv.status_code == 200, rv.json
        assert rv.json[0]["name"] == mapname, rv.json

    client_util.delete_map(username, mapname, client)
