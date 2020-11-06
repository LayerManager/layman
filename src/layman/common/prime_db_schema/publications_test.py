import pytest
import uuid

from test import process, process_client

from layman import settings, app as app
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE
from . import publications, workspaces

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
ensure_layman = process.ensure_layman

userinfo = {"iss_id": 'mock_test',
            "sub": '1',
            "claims": {"email": "test@liferay.com",
                       "name": "test ensure user",
                       "given_name": "test",
                       "family_name": "user",
                       "middle_name": "ensure",
                       }
            }


def test_publication_basic():
    def publications_by_type(prefix,
                             publication_type,
                             ):
        username = prefix + '_username'
        publication_name = prefix + '_pub_name'
        publication_title = prefix + '_pub_ Title'
        publication_title2 = prefix + '_pub_ Title2'

        with app.app_context():
            workspaces.ensure_workspace(username)
            uuid_orig = uuid.uuid4()
            uuid_str = str(uuid_orig)
            db_info = {"name": publication_name,
                       "title": publication_title,
                       "publ_type_name": publication_type,
                       "uuid": uuid_orig,
                       "actor_name": username,
                       }
            publications.insert_publication(username, db_info)
            pubs = publications.get_publication_infos(username, publication_type)
            assert pubs[(username, publication_type, publication_name)].get('name') == publication_name
            assert pubs[(username, publication_type, publication_name)].get('title') == publication_title
            assert pubs[(username, publication_type, publication_name)].get('uuid') == str(uuid_str)

            db_info = {"name": publication_name,
                       "title": publication_title2,
                       "actor_name": username,
                       "publ_type_name": publication_type,
                       }
            publications.update_publication(username, db_info)
            pubs = publications.get_publication_infos(username, publication_type)
            assert pubs[(username, publication_type, publication_name)].get('name') == publication_name
            assert pubs[(username, publication_type, publication_name)].get('title') == publication_title2
            assert pubs[(username, publication_type, publication_name)].get('uuid') == uuid_str

            db_info = {"name": publication_name,
                       "title": publication_title,
                       "actor_name": username,
                       "publ_type_name": publication_type,
                       }
            publications.update_publication(username, db_info)
            pubs = publications.get_publication_infos(username, publication_type)
            assert pubs[(username, publication_type, publication_name)].get('name') == publication_name
            assert pubs[(username, publication_type, publication_name)].get('title') == publication_title
            assert pubs[(username, publication_type, publication_name)].get('uuid') == uuid_str

            publications.delete_publication(username, publication_type, publication_name)
            pubs = publications.get_publication_infos(username, publication_type)
            assert pubs.get((username, publication_type, publication_name)) is None

    publications_by_type('test_publication_basic_layer',
                         LAYER_TYPE)
    publications_by_type('test_publication_basic_map',
                         MAP_TYPE)


@pytest.mark.usefixtures('ensure_layman')
def test_select_publications():
    username = 'test_select_publications_user1'
    layername = 'test_select_publications_layer1'
    mapname = 'test_select_publications_map1'

    process_client.publish_layer(username, layername)
    process_client.publish_map(username, mapname)

    with app.app_context():
        pubs = publications.get_publication_infos(username, LAYER_TYPE)
        assert len(pubs) == 1
        pubs = publications.get_publication_infos(username, MAP_TYPE)
        assert len(pubs) == 1
        pubs = publications.get_publication_infos(username)
        assert len(pubs) == 2
        pubs = publications.get_publication_infos()
        assert len(pubs) >= 2

    process_client.delete_layer(username, layername)
    process_client.delete_map(username, mapname)

    with app.app_context():
        pubs = publications.get_publication_infos(username)
        assert len(pubs) == 0, pubs
