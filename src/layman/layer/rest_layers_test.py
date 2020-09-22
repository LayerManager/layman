import sys

del sys.modules['layman']

from layman import app
from .db import table
from .filesystem import input_file, uuid, input_sld, input_chunk, thumbnail
from .geoserver import wfs, wms, sld
from .micka import soap
from . import util
from layman.util import url_for
from test import client as client_util

client = client_util.client


def test_get_layer_infos(client):
    username = 'test_get_layer_infos_user'
    layername = 'test_get_layer_infos_layer'
    layertitle = "Test get layer infos - layer íářžý"

    client_util.setup_layer_flask(username, layername, client, layertitle)

    result_infos_name = {layername: {'name': layername}}
    result_infos_name_title = {layername: {'name': layername,
                                           'title': layertitle}}
    result_publication_name = [layername]

    with app.app_context():

        modules = [# db.table
                   {'method_infos': table.get_layer_infos,
                    'result_infos': result_infos_name,
                    'method_publications': table.get_publication_names,
                    'result_publications': result_publication_name},
                   # filesystem.input_file
                   {'method_infos': input_file.get_layer_infos,
                    'result_infos': result_infos_name,
                    'method_publications': input_file.get_publication_names,
                    'result_publications': result_publication_name},
                   # filesystem.uuid
                   {'method_infos': uuid.get_layer_infos,
                    'result_infos': result_infos_name,
                    'method_publications': uuid.get_publication_names,
                    'result_publications': result_publication_name},
                   # filesystem.input_sld
                   {'method_infos': input_sld.get_layer_infos,
                    'result_infos': result_infos_name,
                    'method_publications': input_sld.get_publication_names,
                    'result_publications': result_publication_name},
                   # filesystem.input_chunk
                   {'method_infos': input_chunk.get_layer_infos,
                    'result_infos': result_infos_name,
                    'method_publications': input_chunk.get_publication_names,
                    'result_publications': result_publication_name},
                   # filesystem.thumbnail
                   {'method_infos': thumbnail.get_layer_infos,
                    'result_infos': result_infos_name,
                    'method_publications': thumbnail.get_publication_names,
                    'result_publications': result_publication_name},
                   # geoserver.wfs
                   {'method_infos': wfs.get_layer_infos,
                    'result_infos': result_infos_name_title,
                    'method_publications': wfs.get_publication_names,
                    'result_publications': result_publication_name},
                   # geoserver.wms
                   {'method_infos': wms.get_layer_infos,
                    'result_infos': result_infos_name_title,
                    'method_publications': wms.get_publication_names,
                    'result_publications': result_publication_name},
                   # geoserver.sld
                   {'method_infos': sld.get_layer_infos,
                    'result_infos': {},
                    'method_publications': sld.get_publication_names,
                    'result_publications': []},
                   # micka.soap
                   {'method_infos': soap.get_layer_infos,
                    'result_infos': {},
                    'method_publications': soap.get_publication_names,
                    'result_publications': []}
        ]

        for module in modules:
            layer_infos = module["method_infos"](username)
            assert layer_infos == module["result_infos"], layer_infos
            publication_names = module["method_publications"](username, "layman.layer")
            assert publication_names == module["result_publications"], publication_names

        # util
        layer_infos = util.get_layer_infos(username)
        assert layer_infos == result_infos_name_title, layer_infos

    client_util.delete_layer(username, layername)


def test_get_layer_title(client):
    username = 'test_get_layer_infos_user'
    layername = 'test_get_layer_infos_layer'

    client_util.setup_layer_flask(username, layername, client)

    with app.app_context():
        # layers.GET
        rv = client.get(url_for('rest_layers.get', username=username))
        assert rv.status_code == 200, rv.json
        assert rv.json[0]["name"] == layername, rv.json
        assert rv.json[0]["title"] == layername, rv.json

    client_util.delete_layer(username, layername)
