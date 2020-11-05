import sys

del sys.modules['layman']

from layman import app
from .db import table
from .prime_db_schema import table as prime_table
from .filesystem import input_file, uuid, input_sld, input_chunk, thumbnail
from .geoserver import wfs, wms, sld
from .micka import soap
from . import util, LAYER_TYPE
from layman.util import url_for
from test import flask_client as client_util, util as test_util

client = client_util.client


def test_get_layer_infos(client):
    username = 'test_get_layer_infos_user'
    layername = 'test_get_layer_infos_layer'
    layertitle = "Test get layer infos - layer íářžý"

    client_util.publish_layer(username, layername, client, layertitle)

    result_infos_name = {layername: {'name': layername}}
    result_infos_name_title = {layername: {'name': layername,
                                           'title': layertitle}}

    with app.app_context():
        result_infos_name_uuid = {layername: {'name': layername,
                                              'uuid': uuid.get_layer_uuid(username, layername)}}
        result_infos_all = {layername: {'name': layername,
                                        'title': layertitle,
                                        'uuid': uuid.get_layer_uuid(username, layername),
                                        'type': LAYER_TYPE,
                                        # 'can_read': set(),
                                        # 'can_write': set(),
                                        }}
        modules = [
            {'name': 'db.table',
             'method_infos': table.get_layer_infos,
             'result_infos': result_infos_name,
             'method_publications': table.get_publication_infos,
             },
            {'name': 'prime_table.table',
             'method_infos': prime_table.get_layer_infos,
             'result_infos': result_infos_all,
             'method_publications': prime_table.get_publication_infos,
             },
            {'name': 'filesystem.input_file',
             'method_infos': input_file.get_layer_infos,
             'result_infos': result_infos_name,
             'method_publications': input_file.get_publication_infos,
             },
            {'name': 'filesystem.uuid',
             'method_infos': uuid.get_layer_infos,
             'result_infos': result_infos_name_uuid,
             'method_publications': uuid.get_publication_infos,
             },
            {'name': 'filesystem.input_sld',
             'method_infos': input_sld.get_layer_infos,
             'result_infos': result_infos_name,
             'method_publications': input_sld.get_publication_infos,
             },
            {'name': 'filesystem.input_chunk',
             'method_infos': input_chunk.get_layer_infos,
             'result_infos': result_infos_name,
             'method_publications': input_chunk.get_publication_infos,
             },
            {'name': 'filesystem.thumbnail',
             'method_infos': thumbnail.get_layer_infos,
             'result_infos': result_infos_name,
             'method_publications': thumbnail.get_publication_infos,
             },
            {'name': 'geoserver.wfs',
             'method_infos': wfs.get_layer_infos,
             'result_infos': result_infos_name_title,
             'method_publications': wfs.get_publication_infos,
             },
            {'name': 'geoserver.wms',
             'method_infos': wms.get_layer_infos,
             'result_infos': result_infos_name_title,
             'method_publications': wms.get_publication_infos,
             },
            {'name': 'geoserver.sld',
             'method_infos': sld.get_layer_infos,
             'result_infos': {},
             'method_publications': sld.get_publication_infos,
             },
            {'name': 'micka.soap',
             'method_infos': soap.get_layer_infos,
             'result_infos': {},
             'method_publications': soap.get_publication_infos,
             },
        ]

        for module in modules:
            layer_infos = module["method_infos"](username)
            test_util.assert_same_infos(layer_infos, module["result_infos"], module)

            publication_infos = module["method_publications"](username, LAYER_TYPE)
            test_util.assert_same_infos(publication_infos, module["result_infos"], module)

        # util
        layer_infos = util.get_layer_infos(username)
        test_util.assert_same_infos(layer_infos, result_infos_all)

    client_util.delete_layer(username, layername, client)


def test_get_layer_title(client):
    username = 'test_get_layer_infos_user'
    layers = [("c_test_get_layer_infos_layer", "C Test get layer infos - map layer íářžý"),
              ("a_test_get_layer_infos_layer", "A Test get layer infos - map layer íářžý"),
              ("b_test_get_layer_infos_layer", "B Test get layer infos - map layer íářžý")
              ]
    sorted_layers = sorted(layers)

    for (name, title) in layers:
        client_util.publish_layer(username, name, client, title)

    with app.app_context():
        # layers.GET
        rv = client.get(url_for('rest_layers.get', username=username))
        assert rv.status_code == 200, rv.json

        for i in range(0, len(sorted_layers) - 1):
            assert rv.json[i]["name"] == sorted_layers[i][0]
            assert rv.json[i]["title"] == sorted_layers[i][1]

    for (name, title) in layers:
        client_util.delete_layer(username, name, client)
