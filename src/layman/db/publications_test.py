from test.flask_client import client
import test.flask_client as client_util

from layman import settings, app as app
from layman.layer.filesystem import uuid as layer_uuid
from layman.layer import LAYER_TYPE
from layman.map.filesystem import uuid as map_uuid
from layman.map import MAP_TYPE
from . import publications

DB_SCHEMA = settings.PG_LAYMAN_SCHEMA


def test_post_layer(client):
    username = 'test_post_layer_username'
    layername = 'test_post_layer_layer'
    layertitle = 'test_post_layer_layer Title'
    layertitle2 = 'test_post_layer_layer Title2'
    with app.app_context():
        uuid_str = layer_uuid.assign_layer_uuid(username, layername)
        db_info = {"name": layername,
                   "title": layertitle,
                   "publ_type_name": LAYER_TYPE,
                   "uuid": uuid_str,
                   "everyone_can_read": True,
                   "everyone_can_write": True,
                   }
        publications.insert_publication(username, db_info)
        pubs = publications.get_publication_infos(username, LAYER_TYPE)
        assert pubs.get(layername).get('name') == layername
        assert pubs.get(layername).get('title') == layertitle
        assert pubs.get(layername).get('uuid') == uuid_str

        db_info = {"name": layername,
                   "title": layertitle2,
                   "publ_type_name": LAYER_TYPE,
                   "everyone_can_read": False,
                   "everyone_can_write": False
                   }
        publications.update_publication(username, db_info)
        pubs = publications.get_publication_infos(username, LAYER_TYPE)
        assert pubs.get(layername).get('name') == layername
        assert pubs.get(layername).get('title') == layertitle2
        assert pubs.get(layername).get('uuid') == uuid_str
        assert not pubs.get(layername).get('everyone_can_read')
        assert not pubs.get(layername).get('everyone_can_write')
        db_info = {"name": layername,
                   "title": layertitle,
                   "publ_type_name": LAYER_TYPE,
                   }
        publications.update_publication(username, db_info)
        pubs = publications.get_publication_infos(username, LAYER_TYPE)
        assert pubs.get(layername).get('name') == layername
        assert pubs.get(layername).get('title') == layertitle
        assert pubs.get(layername).get('uuid') == uuid_str
        assert not pubs.get(layername).get('everyone_can_read')
        assert not pubs.get(layername).get('everyone_can_write')

        publications.delete_publication(username, layername, LAYER_TYPE)
        pubs = publications.get_publication_infos(username, LAYER_TYPE)
        assert pubs.get(layername) is None

        client_util.delete_layer(username, layername, client)


def test_post_map(client):
    username = 'test_post_map_username'
    mapname = 'test_post_map_map'
    maptitle = 'test_post_map_map Title'
    maptitle2 = 'test_post_map_map Title2'
    with app.app_context():
        uuid_str = map_uuid.assign_map_uuid(username, mapname)
        db_info = {"name": mapname,
                   "title": maptitle,
                   "publ_type_name": MAP_TYPE,
                   "uuid": uuid_str,
                   "everyone_can_read": True,
                   "everyone_can_write": True,
                   }
        publications.insert_publication(username, db_info)
        pubs = publications.get_publication_infos(username, MAP_TYPE)
        assert pubs.get(mapname).get('name') == mapname
        assert pubs.get(mapname).get('title') == maptitle
        assert pubs.get(mapname).get('uuid') == uuid_str

        db_info = {"name": mapname,
                   "title": maptitle2,
                   "publ_type_name": MAP_TYPE,
                   "everyone_can_read": False,
                   "everyone_can_write": False
                   }
        publications.update_publication(username, db_info)
        pubs = publications.get_publication_infos(username, MAP_TYPE)
        assert pubs.get(mapname).get('name') == mapname
        assert pubs.get(mapname).get('title') == maptitle2
        assert pubs.get(mapname).get('uuid') == uuid_str
        assert not pubs.get(mapname).get('everyone_can_read')
        assert not pubs.get(mapname).get('everyone_can_write')
        db_info = {"name": mapname,
                   "title": maptitle,
                   "publ_type_name": MAP_TYPE,
                   }
        publications.update_publication(username, db_info)
        pubs = publications.get_publication_infos(username, MAP_TYPE)
        assert pubs.get(mapname).get('name') == mapname
        assert pubs.get(mapname).get('title') == maptitle
        assert pubs.get(mapname).get('uuid') == uuid_str
        assert not pubs.get(mapname).get('everyone_can_read')
        assert not pubs.get(mapname).get('everyone_can_write')

        publications.delete_publication(username, mapname, MAP_TYPE)
        pubs = publications.get_publication_infos(username, MAP_TYPE)
        assert pubs.get(mapname) is None

        client_util.delete_map(username, mapname, client)


def test_select_publications(client):
    username = 'test_select_publications_user1'
    layername = 'test_select_publications_layer1'
    mapname = 'test_select_publications_map1'
    with app.app_context():
        client_util.publish_layer(username, layername, client)
        client_util.publish_map(username, mapname, client)

        pubs = publications.get_publication_infos(username, 'layman.layer')
        assert len(pubs) == 1
        pubs = publications.get_publication_infos(username, 'layman.map')
        assert len(pubs) == 1
        pubs = publications.get_publication_infos(username)
        assert len(pubs) == 2
        pubs = publications.get_publication_infos()
        assert len(pubs) >= 2

        client_util.delete_layer(username, layername, client)
        client_util.delete_map(username, mapname, client)

        pubs = publications.get_publication_infos(username, LAYER_TYPE)
        assert pubs.get(layername) is None
