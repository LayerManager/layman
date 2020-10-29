import pytest

from test import process, process_client

from layman import settings, app as app, LaymanError
from layman.layer.filesystem import uuid as layer_uuid
from layman.layer import LAYER_TYPE
from layman.map.filesystem import uuid as map_uuid
from layman.map import MAP_TYPE
from . import publications, workspaces, users

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
ensure_layman = process.ensure_layman


def test_post_layer(ensure_layman):
    username = 'test_post_layer_username'
    layername = 'test_post_layer_layer'
    layertitle = 'test_post_layer_layer Title'
    layertitle2 = 'test_post_layer_layer Title2'

    with app.app_context():
        workspaces.ensure_workspace(username)
        uuid_str = layer_uuid.assign_layer_uuid(username, layername)
        db_info = {"name": layername,
                   "title": layertitle,
                   "publ_type_name": LAYER_TYPE,
                   "uuid": uuid_str,
                   "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                     "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                     }
                   }
        publications.insert_publication(username, db_info)
        pubs = publications.get_publication_infos(username, LAYER_TYPE)
        assert pubs.get(layername).get('name') == layername
        assert pubs.get(layername).get('title') == layertitle
        assert pubs.get(layername).get('uuid') == uuid_str
        # assert settings.RIGHTS_EVERYONE_ROLE in pubs.get(layername).get('can_read')
        # assert settings.RIGHTS_EVERYONE_ROLE in pubs.get(layername).get('can_write')

        db_info = {"name": layername,
                   "title": layertitle2,
                   "publ_type_name": LAYER_TYPE,
                   "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                     "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                     }
                   }
        publications.update_publication(username, db_info)
        pubs = publications.get_publication_infos(username, LAYER_TYPE)
        assert pubs.get(layername).get('name') == layername
        assert pubs.get(layername).get('title') == layertitle2
        assert pubs.get(layername).get('uuid') == uuid_str
        # assert settings.RIGHTS_EVERYONE_ROLE in pubs.get(layername).get('can_read')
        # assert settings.RIGHTS_EVERYONE_ROLE in pubs.get(layername).get('can_write')
        db_info = {"name": layername,
                   "title": layertitle,
                   "publ_type_name": LAYER_TYPE,
                   "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                     "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                     }
                   }
        publications.update_publication(username, db_info)
        pubs = publications.get_publication_infos(username, LAYER_TYPE)
        assert pubs.get(layername).get('name') == layername
        assert pubs.get(layername).get('title') == layertitle
        assert pubs.get(layername).get('uuid') == uuid_str
        # assert settings.RIGHTS_EVERYONE_ROLE in pubs.get(layername).get('can_read')
        # assert settings.RIGHTS_EVERYONE_ROLE in pubs.get(layername).get('can_write')

        publications.delete_publication(username, layername, LAYER_TYPE)
        pubs = publications.get_publication_infos(username, LAYER_TYPE)
        assert pubs.get(layername) is None

    process_client.delete_layer(username, layername)


def test_post_map(ensure_layman):
    username = 'test_post_map_username'
    mapname = 'test_post_map_map'
    maptitle = 'test_post_map_map Title'
    maptitle2 = 'test_post_map_map Title2'

    with app.app_context():
        workspaces.ensure_workspace(username)
        uuid_str = map_uuid.assign_map_uuid(username, mapname)
        db_info = {"name": mapname,
                   "title": maptitle,
                   "publ_type_name": MAP_TYPE,
                   "uuid": uuid_str,
                   "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                     "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                     }
                   }
        publications.insert_publication(username, db_info)
        pubs = publications.get_publication_infos(username, MAP_TYPE)
        assert pubs.get(mapname).get('name') == mapname
        assert pubs.get(mapname).get('title') == maptitle
        assert pubs.get(mapname).get('uuid') == uuid_str
        # assert settings.RIGHTS_EVERYONE_ROLE in pubs.get(mapname).get('can_read')
        # assert settings.RIGHTS_EVERYONE_ROLE in pubs.get(mapname).get('can_write')

        db_info = {"name": mapname,
                   "title": maptitle2,
                   "publ_type_name": MAP_TYPE,
                   "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                     "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                     }
                   }
        publications.update_publication(username, db_info)
        pubs = publications.get_publication_infos(username, MAP_TYPE)
        assert pubs.get(mapname).get('name') == mapname
        assert pubs.get(mapname).get('title') == maptitle2
        assert pubs.get(mapname).get('uuid') == uuid_str
        # assert settings.RIGHTS_EVERYONE_ROLE in pubs.get(mapname).get('can_read')
        # assert settings.RIGHTS_EVERYONE_ROLE in pubs.get(mapname).get('can_write')
        db_info = {"name": mapname,
                   "title": maptitle,
                   "publ_type_name": MAP_TYPE,
                   "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                     "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                     }
                   }
        publications.update_publication(username, db_info)
        pubs = publications.get_publication_infos(username, MAP_TYPE)
        assert pubs.get(mapname).get('name') == mapname
        assert pubs.get(mapname).get('title') == maptitle
        assert pubs.get(mapname).get('uuid') == uuid_str
        # assert settings.RIGHTS_EVERYONE_ROLE in pubs.get(mapname).get('can_read')
        # assert settings.RIGHTS_EVERYONE_ROLE in pubs.get(mapname).get('can_write')

        publications.delete_publication(username, mapname, MAP_TYPE)
        pubs = publications.get_publication_infos(username, MAP_TYPE)
        assert pubs.get(mapname) is None

    process_client.delete_map(username, mapname)


def test_select_publications(ensure_layman):
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
        assert pubs.get(layername) is None


def test_only_valid_names(ensure_layman):
    workspace_name = 'test_only_valid_names_workspace'
    username = 'test_only_valid_names_user'
    userinfo = {"iss_id": 'mock_test',
                "sub": '1',
                "claims": {"email": "test@liferay.com",
                           "name": "test ensure user",
                           "given_name": "test",
                           "family_name": "user",
                           "middle_name": "ensure",
                           }
                }

    with app.app_context():
        id_workspace = workspaces.ensure_workspace(workspace_name)
        id_workspace_user = workspaces.ensure_workspace(username)
        user_id = users.ensure_user(id_workspace_user, userinfo)

        publications.only_valid_names(set())
        publications.only_valid_names({username, })
        publications.only_valid_names({settings.RIGHTS_EVERYONE_ROLE, })
        publications.only_valid_names({settings.RIGHTS_EVERYONE_ROLE, username, })
        publications.only_valid_names({username, settings.RIGHTS_EVERYONE_ROLE, })

        with pytest.raises(LaymanError) as exc_info:
            publications.only_valid_names({username, workspace_name})
            assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            publications.only_valid_names({workspace_name, username})
            assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            publications.only_valid_names({workspace_name, settings.RIGHTS_EVERYONE_ROLE, })
            assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            publications.only_valid_names({settings.RIGHTS_EVERYONE_ROLE, 'skaljgdalskfglshfgd', })
            assert exc_info.value.code == 43


def test_at_least_one_can_write(ensure_layman):
    workspace_name = 'test_at_least_one_can_write_workspace'
    username = 'test_at_least_one_can_write_user'

    publications.at_least_one_can_write({username, })
    publications.at_least_one_can_write({settings.RIGHTS_EVERYONE_ROLE, })
    publications.at_least_one_can_write({username, settings.RIGHTS_EVERYONE_ROLE, })
    publications.at_least_one_can_write({workspace_name, })
    publications.at_least_one_can_write({'lusfjdiaurghalskug', })

    with pytest.raises(LaymanError) as exc_info:
        publications.at_least_one_can_write(set())
        assert exc_info.value.code == 43


def test_who_can_write_can_read(ensure_layman):
    workspace_name = 'test_who_can_write_can_read_workspace'
    username = 'test_who_can_write_can_read_user'

    publications.who_can_write_can_read(set(), set())
    publications.who_can_write_can_read({username, }, {username, })
    publications.who_can_write_can_read({username, workspace_name}, {username, })
    publications.who_can_write_can_read({username, settings.RIGHTS_EVERYONE_ROLE}, {username, })
    publications.who_can_write_can_read({username, settings.RIGHTS_EVERYONE_ROLE}, {username, settings.RIGHTS_EVERYONE_ROLE, })
    publications.who_can_write_can_read({settings.RIGHTS_EVERYONE_ROLE, }, {settings.RIGHTS_EVERYONE_ROLE, })
    publications.who_can_write_can_read({settings.RIGHTS_EVERYONE_ROLE, }, {settings.RIGHTS_EVERYONE_ROLE, username, })
    publications.who_can_write_can_read({settings.RIGHTS_EVERYONE_ROLE, }, {settings.RIGHTS_EVERYONE_ROLE, workspace_name, })
    publications.who_can_write_can_read({settings.RIGHTS_EVERYONE_ROLE, username, }, {settings.RIGHTS_EVERYONE_ROLE, })
    publications.who_can_write_can_read({settings.RIGHTS_EVERYONE_ROLE, username, }, set())
    publications.who_can_write_can_read({workspace_name, }, {workspace_name, })

    with pytest.raises(LaymanError) as exc_info:
        publications.who_can_write_can_read(set(), {workspace_name, })
        assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.who_can_write_can_read(set(), {username, })
        assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.who_can_write_can_read(set(), {settings.RIGHTS_EVERYONE_ROLE, })
        assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.who_can_write_can_read(username, {settings.RIGHTS_EVERYONE_ROLE, })
        assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.who_can_write_can_read(username, {workspace_name, })
        assert exc_info.value.code == 43


def test_i_can_still_write(ensure_layman):
    workspace_name = 'test_i_can_still_write_workspace'
    username = 'test_test_who_can_write_can_read'

    publications.i_can_still_write(None, {settings.RIGHTS_EVERYONE_ROLE, })
    publications.i_can_still_write(None, {username, settings.RIGHTS_EVERYONE_ROLE, })
    publications.i_can_still_write(username, {settings.RIGHTS_EVERYONE_ROLE, })
    publications.i_can_still_write(username, {workspace_name, settings.RIGHTS_EVERYONE_ROLE, })
    publications.i_can_still_write(username, {workspace_name, username, })

    with pytest.raises(LaymanError) as exc_info:
        publications.i_can_still_write(None, set())
        assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.i_can_still_write(None, {workspace_name, })
        assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.i_can_still_write(username, set())
        assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.i_can_still_write(username, {workspace_name, })
        assert exc_info.value.code == 43
