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

    client_util.setup_layer_flask(username, layername, client)

    with app.app_context():

        # db.table
        layer_infos = table.get_layer_infos(username)
        assert layer_infos == {layername: {'name': layername}}, layer_infos
        publication_names = table.get_publication_names(username, "layman.layer")
        assert publication_names == [layername]

        # filesystem.input_file
        layer_infos = input_file.get_layer_infos(username)
        assert layer_infos == {layername: {'name': layername}}, layer_infos
        publication_names = input_file.get_publication_names(username, "layman.layer")
        assert publication_names == [layername]

        # filesystem.uuid
        layer_infos = uuid.get_layer_infos(username)
        assert layer_infos == {layername: {'name': layername}}, layer_infos
        publication_names = uuid.get_publication_names(username, "layman.layer")
        assert publication_names == [layername]

        # filesystem.input_sld
        layer_infos = input_sld.get_layer_infos(username)
        assert layer_infos == {layername: {'name': layername}}, layer_infos
        publication_names = input_sld.get_publication_names(username, "layman.layer")
        assert publication_names == [layername]

        # filesystem.input_chunk
        layer_infos = input_chunk.get_layer_infos(username)
        assert layer_infos == {layername: {'name': layername}}, layer_infos
        publication_names = input_chunk.get_publication_names(username, "layman.layer")
        assert publication_names == [layername]

        # filesystem.thumbnail
        layer_infos = thumbnail.get_layer_infos(username)
        assert layer_infos == {layername: {'name': layername}}, layer_infos
        publication_names = thumbnail.get_publication_names(username, "layman.layer")
        assert publication_names == [layername]

        # geoserver.wfs
        layer_infos = wfs.get_layer_infos(username)
        assert layer_infos == {layername: {'name': layername,
                                           'title': layername}}, layer_infos
        publication_names = wfs.get_publication_names(username, "layman.layer")
        assert publication_names == [layername]

        # geoserver.wms
        layer_infos = wms.get_layer_infos(username)
        assert layer_infos == {layername: {'name': layername,
                                           'title': layername}}, layer_infos
        publication_names = wms.get_publication_names(username, "layman.layer")
        assert publication_names == [layername]

        # geoserver.sld
        layer_infos = sld.get_layer_infos(username)
        assert layer_infos == {}, layer_infos
        publication_names = sld.get_publication_names(username, "layman.layer")
        assert publication_names == []

        # micka.soap
        layer_infos = soap.get_layer_infos(username)
        assert layer_infos == {}, layer_infos
        publication_names = soap.get_publication_names(username, "layman.layer")
        assert publication_names == []

        # util
        layer_infos = util.get_layer_infos(username)
        assert layer_infos == {layername: {'name': layername,
                                           'title': layername}}, layer_infos

    client_util.delete_layer(username, layername)


def test_get_layer_title(client):
    username = 'test_get_layer_infos_user'
    layername = 'test_get_layer_infos_layer'

    client_util.setup_layer_flask(username, layername, client)

    with app.app_context():
        # layers.GET
        rv = client.get(url_for('rest_layers.get', username=username))
        assert rv.status_code == 200, rv.json
        print(rv.json)
        assert rv.json[0]["name"] == layername, rv.json
        assert rv.json[0]["title"] == layername, rv.json

    client_util.delete_layer(username, layername)
