import pytest
import uuid

from test import process, process_client

from layman import settings, app as app, LaymanError
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE
from . import publications, workspaces, users

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
ensure_layman = process.ensure_layman


@pytest.mark.usefixtures('ensure_layman')
def test_post_layer():
    username = 'test_post_layer_username'
    layername = 'test_post_layer_layer'
    layertitle = 'test_post_layer_layer Title'
    layertitle2 = 'test_post_layer_layer Title2'

    with app.app_context():
        workspaces.ensure_workspace(username)
        uuid_orig = uuid.uuid4()
        uuid_str = str(uuid_orig)
        db_info = {"name": layername,
                   "title": layertitle,
                   "publ_type_name": LAYER_TYPE,
                   "uuid": uuid_orig,
                   "actor_name": username,
                   "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                     "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                     }
                   }
        publications.insert_publication(username, db_info)
        pubs = publications.get_publication_infos(username, LAYER_TYPE)
        assert pubs[(username, layername, LAYER_TYPE)].get('name') == layername
        assert pubs[(username, layername, LAYER_TYPE)].get('title') == layertitle
        assert pubs[(username, layername, LAYER_TYPE)].get('uuid') == str(uuid_str)

        db_info = {"name": layername,
                   "title": layertitle2,
                   "actor_name": username,
                   "publ_type_name": LAYER_TYPE,
                   "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                     "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                     }
                   }
        publications.update_publication(username, db_info)
        pubs = publications.get_publication_infos(username, LAYER_TYPE)
        assert pubs[(username, layername, LAYER_TYPE)].get('name') == layername
        assert pubs[(username, layername, LAYER_TYPE)].get('title') == layertitle2
        assert pubs[(username, layername, LAYER_TYPE)].get('uuid') == uuid_str

        db_info = {"name": layername,
                   "title": layertitle,
                   "actor_name": username,
                   "publ_type_name": LAYER_TYPE,
                   "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                     "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                     }
                   }
        publications.update_publication(username, db_info)
        pubs = publications.get_publication_infos(username, LAYER_TYPE)
        assert pubs[(username, layername, LAYER_TYPE)].get('name') == layername
        assert pubs[(username, layername, LAYER_TYPE)].get('title') == layertitle
        assert pubs[(username, layername, LAYER_TYPE)].get('uuid') == uuid_str

        publications.delete_publication(username, layername, LAYER_TYPE)
        pubs = publications.get_publication_infos(username, LAYER_TYPE)
        assert pubs.get((username, layername, LAYER_TYPE)) is None


@pytest.mark.usefixtures('ensure_layman')
def test_post_map():
    username = 'test_post_map_username'
    mapname = 'test_post_map_map'
    maptitle = 'test_post_map_map Title'
    maptitle2 = 'test_post_map_map Title2'

    with app.app_context():
        workspaces.ensure_workspace(username)
        uuid_orig = uuid.uuid4()
        uuid_str = str(uuid_orig)
        db_info = {"name": mapname,
                   "title": maptitle,
                   "publ_type_name": MAP_TYPE,
                   "actor_name": username,
                   "uuid": uuid_orig,
                   "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                     "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                     }
                   }
        publications.insert_publication(username, db_info)
        pubs = publications.get_publication_infos(username, MAP_TYPE)
        assert pubs[(username, mapname, MAP_TYPE)].get('name') == mapname
        assert pubs[(username, mapname, MAP_TYPE)].get('title') == maptitle
        assert pubs[(username, mapname, MAP_TYPE)].get('uuid') == uuid_str

        db_info = {"name": mapname,
                   "title": maptitle2,
                   "publ_type_name": MAP_TYPE,
                   "actor_name": username,
                   "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                     "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                     }
                   }
        publications.update_publication(username, db_info)
        pubs = publications.get_publication_infos(username, MAP_TYPE)
        assert pubs[(username, mapname, MAP_TYPE)].get('name') == mapname
        assert pubs[(username, mapname, MAP_TYPE)].get('title') == maptitle2
        assert pubs[(username, mapname, MAP_TYPE)].get('uuid') == uuid_str

        db_info = {"name": mapname,
                   "title": maptitle,
                   "publ_type_name": MAP_TYPE,
                   "actor_name": username,
                   "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                     "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                     }
                   }
        publications.update_publication(username, db_info)
        pubs = publications.get_publication_infos(username, MAP_TYPE)
        assert pubs[(username, mapname, MAP_TYPE)].get('name') == mapname
        assert pubs[(username, mapname, MAP_TYPE)].get('title') == maptitle
        assert pubs[(username, mapname, MAP_TYPE)].get('uuid') == uuid_str

        publications.delete_publication(username, mapname, MAP_TYPE)
        pubs = publications.get_publication_infos(username, MAP_TYPE)
        assert pubs.get((username, mapname, MAP_TYPE)) is None


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


def test_only_valid_names():
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
        workspaces.ensure_workspace(workspace_name)
        id_workspace_user = workspaces.ensure_workspace(username)
        users.ensure_user(id_workspace_user, userinfo)

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


def test_at_least_one_can_write():
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


def test_who_can_write_can_read():
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


def test_i_can_still_write():
    workspace_name = 'test_i_can_still_write_workspace'
    username = 'test_who_can_write_can_read_user'

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


def test_owner_can_still_write():
    workspace_name = 'test_owner_can_still_write_workspace'
    username = 'test_owner_can_still_write_user'

    publications.owner_can_still_write(None, set())
    publications.owner_can_still_write(None, {settings.RIGHTS_EVERYONE_ROLE, })
    publications.owner_can_still_write(None, {username, })
    publications.owner_can_still_write(username, {settings.RIGHTS_EVERYONE_ROLE, })
    publications.owner_can_still_write(username, {username, })
    publications.owner_can_still_write(username, {username, workspace_name, })

    with pytest.raises(LaymanError) as exc_info:
        publications.owner_can_still_write(username, set())
        assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.owner_can_still_write(username, {workspace_name, })
        assert exc_info.value.code == 43


def test_clear_roles():
    workspace_name = 'test_clear_roles_workspace'
    username = 'test_clear_roles_user'
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
        workspaces.ensure_workspace(workspace_name)
        id_workspace_user = workspaces.ensure_workspace(username)
        users.ensure_user(id_workspace_user, userinfo)

        list = publications.clear_roles({username, }, workspace_name)
        assert list == {username, }, list

        list = publications.clear_roles({username, workspace_name, }, workspace_name)
        assert list == {username, workspace_name, }, list

        list = publications.clear_roles({username, }, username)
        assert list == set(), list

        list = publications.clear_roles({username, workspace_name, }, username)
        assert list == {workspace_name, }, list

        list = publications.clear_roles({username, settings.RIGHTS_EVERYONE_ROLE, }, workspace_name)
        assert list == {username, }, list

        list = publications.clear_roles({username, settings.RIGHTS_EVERYONE_ROLE, }, username)
        assert list == set(), list


def assert_access_rights(workspace_name,
                         publication_name,
                         publication_type,
                         read_to_test,
                         write_to_test):
    pubs = publications.get_publication_infos(workspace_name, publication_type)
    assert pubs[(workspace_name, publication_name, publication_type)]["access_rights"]["read"] == read_to_test
    assert pubs[(workspace_name, publication_name, publication_type)]["access_rights"]["write"] == write_to_test


def test_insert_rights():
    def case_test_insert_rights(username,
                                publication_info_original,
                                access_rights,
                                read_to_test,
                                write_to_test,
                                ):
        publication_info = publication_info_original.copy()
        publication_info.update({"access_rights": access_rights})
        if users.get_user_infos(username):
            publication_info.update({"actor_name": username})
        publications.insert_publication(username, publication_info)
        assert_access_rights(username,
                             publication_info_original["name"],
                             publication_info_original["publ_type_name"],
                             read_to_test,
                             write_to_test,
                             )
        publications.delete_publication(username, publication_info["name"], publication_info["publ_type_name"])

    workspace_name = 'test_insert_rights_workspace'
    username = 'test_insert_rights_user'
    username2 = 'test_insert_rights_user2'
    userinfo = {"iss_id": 'mock_test',
                "sub": '1',
                "claims": {"email": "test@liferay.com",
                           "name": "test ensure user",
                           "given_name": "test",
                           "family_name": "user",
                           "middle_name": "ensure",
                           }
                }
    publication_name = 'test_insert_rights_publication_name'
    publication_type = MAP_TYPE

    with app.app_context():
        workspaces.ensure_workspace(workspace_name)
        id_workspace_user = workspaces.ensure_workspace(username)
        users.ensure_user(id_workspace_user, userinfo)
        id_workspace_user2 = workspaces.ensure_workspace(username2)
        users.ensure_user(id_workspace_user2, userinfo)

        publication_info = {"name": publication_name,
                            "title": publication_name,
                            "actor_name": username,
                            "publ_type_name": publication_type,
                            "uuid": uuid.uuid4(),
                            }

        case_test_insert_rights(username,
                                publication_info,
                                {"read": {username, },
                                 "write": {username, },
                                 },
                                {username, },
                                {username, },
                                )

        case_test_insert_rights(username,
                                publication_info,
                                {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                 "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                 },
                                {username, settings.RIGHTS_EVERYONE_ROLE, },
                                {username, settings.RIGHTS_EVERYONE_ROLE, },
                                )

        case_test_insert_rights(username,
                                publication_info,
                                {"read": {settings.RIGHTS_EVERYONE_ROLE, username, },
                                 "write": {settings.RIGHTS_EVERYONE_ROLE, username, },
                                 },
                                {username, settings.RIGHTS_EVERYONE_ROLE, },
                                {username, settings.RIGHTS_EVERYONE_ROLE, },
                                )

        case_test_insert_rights(username,
                                publication_info,
                                {"read": {username, username2, },
                                 "write": {username, username2, },
                                 },
                                {username, username2, },
                                {username, username2, },
                                )

        case_test_insert_rights(workspace_name,
                                publication_info,
                                {"read": {settings.RIGHTS_EVERYONE_ROLE, username, },
                                 "write": {settings.RIGHTS_EVERYONE_ROLE, username, },
                                 },
                                {username, settings.RIGHTS_EVERYONE_ROLE, },
                                {username, settings.RIGHTS_EVERYONE_ROLE, },
                                )

        case_test_insert_rights(workspace_name,
                                publication_info,
                                {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                 "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                 },
                                {settings.RIGHTS_EVERYONE_ROLE, },
                                {settings.RIGHTS_EVERYONE_ROLE, },
                                )


def test_update_rights():
    def case_test_update_rights(username,
                                publication_info_original,
                                publication_update_info,
                                read_to_test,
                                write_to_test,
                                ):
        if not publication_update_info.get("publ_type_name"):
            publication_update_info["publ_type_name"] = publication_info_original["publ_type_name"]
        if not publication_update_info.get("name"):
            publication_update_info["name"] = publication_info_original["name"]
        publications.update_publication(username,
                                        publication_update_info,
                                        )
        assert_access_rights(username,
                             publication_info_original["name"],
                             publication_info_original["publ_type_name"],
                             read_to_test,
                             write_to_test,
                             )

    workspace_name = 'test_update_rights_workspace'
    username = 'test_update_rights_user'
    username2 = 'test_update_rights_user2'
    userinfo = {"iss_id": 'mock_test',
                "sub": '1',
                "claims": {"email": "test@liferay.com",
                           "name": "test ensure user",
                           "given_name": "test",
                           "family_name": "user",
                           "middle_name": "ensure",
                           }
                }
    publication_name = 'test_update_rights_publication_name'
    publication_type = MAP_TYPE
    publication_insert_info = {"name": publication_name,
                               "title": publication_name,
                               "publ_type_name": publication_type,
                               "actor_name": username,
                               "uuid": uuid.uuid4(),
                               "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                                 "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                                 },
                               'actor_name': username
                               }

    with app.app_context():
        workspaces.ensure_workspace(workspace_name)
        id_workspace_user = workspaces.ensure_workspace(username)
        users.ensure_user(id_workspace_user, userinfo)
        id_workspace_user2 = workspaces.ensure_workspace(username2)
        users.ensure_user(id_workspace_user2, userinfo)

        publications.insert_publication(username, publication_insert_info)

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   },
                                 'actor_name': username},
                                {username, settings.RIGHTS_EVERYONE_ROLE, },
                                {username, settings.RIGHTS_EVERYONE_ROLE, },
                                )

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {username, username2, },
                                                   "write": {username, username2, },
                                                   },
                                 'actor_name': username},
                                {username, username2, },
                                {username, username2, },
                                )

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   },
                                 'actor_name': username},
                                {username, settings.RIGHTS_EVERYONE_ROLE, },
                                {username, settings.RIGHTS_EVERYONE_ROLE, },
                                )

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {username, },
                                                   "write": {username, },
                                                   },
                                 'actor_name': username},
                                {username, },
                                {username, },
                                )

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   },
                                 'actor_name': None},
                                {username, settings.RIGHTS_EVERYONE_ROLE, },
                                {username, settings.RIGHTS_EVERYONE_ROLE, },
                                )

        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"read": {username2, },
                                                       "write": {username2, },
                                                       },
                                     'actor_name': username2},
                                    {username, username2, },
                                    {username, username2, },
                                    )
            assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"read": {username, },
                                                       },
                                     'actor_name': username},
                                    {username, username2, },
                                    {username, username2, },
                                    )
            assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"read": {username, },
                                                       },
                                     'actor_name': username},
                                    {username, username2, },
                                    {username, username2, },
                                    )
            assert exc_info.value.code == 43

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {username, },
                                                   "write": {username, },
                                                   },
                                 'actor_name': username},
                                {username, },
                                {username, },
                                )
        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"write": {username, username2, },
                                                       },
                                     'actor_name': username},
                                    {username, username2, },
                                    {username, username2, username2, },
                                    )
            assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"write": {settings.RIGHTS_EVERYONE_ROLE, },
                                                       },
                                     'actor_name': username},
                                    {username, username2, },
                                    {settings.RIGHTS_EVERYONE_ROLE, },
                                    )
            assert exc_info.value.code == 43

        publications.delete_publication(username, publication_insert_info["name"], publication_insert_info["publ_type_name"])


@pytest.mark.usefixtures('ensure_layman')
def test_publications_same_name():
    publ_name = 'test_publications_same_name_publ'
    username = 'test_publications_same_name_user'
    username2 = 'test_publications_same_name_user2'

    process_client.publish_layer(username, publ_name)
    process_client.publish_map(username, publ_name)
    process_client.publish_layer(username2, publ_name)
    process_client.publish_map(username2, publ_name)

    with app.app_context():
        pubs = publications.get_publication_infos(username)
        assert len(pubs) == 2
        pubs = publications.get_publication_infos(username2)
        assert len(pubs) == 2
        pubs = publications.get_publication_infos()
        assert len(pubs) >= 4

    process_client.delete_layer(username, publ_name)
    process_client.delete_map(username, publ_name)
    process_client.delete_layer(username2, publ_name)
    process_client.delete_map(username2, publ_name)


@pytest.mark.usefixtures('ensure_layman')
def test_layer_rights():
    workspace_name = 'test_layer_rights_workspace'
    username = 'test_layer_rights_user'
    username2 = 'test_layer_rights_user2'
    userinfo = {"iss_id": 'mock_test',
                "sub": '1',
                "claims": {"email": "test@liferay.com",
                           "name": "test ensure user",
                           "given_name": "test",
                           "family_name": "user",
                           "middle_name": "ensure",
                           }
                }
    publication_name = 'test_layer_rights_layer'
    publication_type = LAYER_TYPE

    with app.app_context():
        workspaces.ensure_workspace(workspace_name)
        id_workspace_user = workspaces.ensure_workspace(username)
        users.ensure_user(id_workspace_user, userinfo)
        id_workspace_user2 = workspaces.ensure_workspace(username2)
        users.ensure_user(id_workspace_user2, userinfo)

        process_client.publish_layer(workspace_name,
                                     publication_name,
                                     access_rights={'read': f'{settings.RIGHTS_EVERYONE_ROLE}, {username2}',
                                                    'write': f'{settings.RIGHTS_EVERYONE_ROLE}, {username2}'})
        info = publications.get_publication_infos(workspace_name, publication_type)[(workspace_name, publication_name, publication_type)]
        assert info['access_rights']['read'] == {username2, settings.RIGHTS_EVERYONE_ROLE}
        assert info['access_rights']['write'] == {username2, settings.RIGHTS_EVERYONE_ROLE}

        process_client.patch_layer(workspace_name,
                                   publication_name,
                                   access_rights={'read': f'{settings.RIGHTS_EVERYONE_ROLE}'})
        info = publications.get_publication_infos(workspace_name, publication_type)[(workspace_name, publication_name, publication_type)]
        assert info['access_rights']['read'] == {settings.RIGHTS_EVERYONE_ROLE}
        assert info['access_rights']['write'] == {username2, settings.RIGHTS_EVERYONE_ROLE}

        process_client.patch_layer(workspace_name,
                                   publication_name,
                                   access_rights={'write': f'{settings.RIGHTS_EVERYONE_ROLE}'})
        info = publications.get_publication_infos(workspace_name, publication_type)[(workspace_name, publication_name, publication_type)]
        assert info['access_rights']['read'] == {settings.RIGHTS_EVERYONE_ROLE}
        assert info['access_rights']['write'] == {settings.RIGHTS_EVERYONE_ROLE}

        process_client.patch_layer(workspace_name,
                                   publication_name,
                                   access_rights={'read': f'{settings.RIGHTS_EVERYONE_ROLE}, {username}',
                                                  'write': f'{settings.RIGHTS_EVERYONE_ROLE}, {username}'})
        info = publications.get_publication_infos(workspace_name, publication_type)[(workspace_name, publication_name, publication_type)]
        assert info['access_rights']['read'] == {username, settings.RIGHTS_EVERYONE_ROLE}
        assert info['access_rights']['write'] == {username, settings.RIGHTS_EVERYONE_ROLE}

        process_client.delete_layer(workspace_name, publication_name)


@pytest.mark.usefixtures('ensure_layman')
def test_map_rights():
    workspace_name = 'test_map_rights_workspace'
    username = 'test_map_rights_user'
    username2 = 'test_map_rights_user2'
    userinfo = {"iss_id": 'mock_test',
                "sub": '1',
                "claims": {"email": "test@liferay.com",
                           "name": "test ensure user",
                           "given_name": "test",
                           "family_name": "user",
                           "middle_name": "ensure",
                           }
                }
    publication_name = 'test_maprights_layer'
    publication_type = MAP_TYPE

    with app.app_context():
        workspaces.ensure_workspace(workspace_name)
        id_workspace_user = workspaces.ensure_workspace(username)
        users.ensure_user(id_workspace_user, userinfo)
        id_workspace_user2 = workspaces.ensure_workspace(username2)
        users.ensure_user(id_workspace_user2, userinfo)

        process_client.publish_map(workspace_name,
                                   publication_name,
                                   access_rights={'read': f'{settings.RIGHTS_EVERYONE_ROLE}, {username2}',
                                                  'write': f'{settings.RIGHTS_EVERYONE_ROLE}, {username2}'})
        info = publications.get_publication_infos(workspace_name, publication_type)[(workspace_name, publication_name, publication_type)]
        assert info['access_rights']['read'] == {username2, settings.RIGHTS_EVERYONE_ROLE}
        assert info['access_rights']['write'] == {username2, settings.RIGHTS_EVERYONE_ROLE}

        process_client.patch_map(workspace_name,
                                 publication_name,
                                 access_rights={'read': f'{settings.RIGHTS_EVERYONE_ROLE}'})
        info = publications.get_publication_infos(workspace_name, publication_type)[(workspace_name, publication_name, publication_type)]
        assert info['access_rights']['read'] == {settings.RIGHTS_EVERYONE_ROLE}
        assert info['access_rights']['write'] == {username2, settings.RIGHTS_EVERYONE_ROLE}

        process_client.patch_map(workspace_name,
                                 publication_name,
                                 access_rights={'write': f'{settings.RIGHTS_EVERYONE_ROLE}'})
        info = publications.get_publication_infos(workspace_name, publication_type)[(workspace_name, publication_name, publication_type)]
        assert info['access_rights']['read'] == {settings.RIGHTS_EVERYONE_ROLE}
        assert info['access_rights']['write'] == {settings.RIGHTS_EVERYONE_ROLE}

        process_client.patch_map(workspace_name,
                                 publication_name,
                                 access_rights={'read': f'{settings.RIGHTS_EVERYONE_ROLE}, {username}',
                                                'write': f'{settings.RIGHTS_EVERYONE_ROLE}, {username}'})
        info = publications.get_publication_infos(workspace_name, publication_type)[(workspace_name, publication_name, publication_type)]
        assert info['access_rights']['read'] == {username, settings.RIGHTS_EVERYONE_ROLE}
        assert info['access_rights']['write'] == {username, settings.RIGHTS_EVERYONE_ROLE}

        process_client.delete_map(workspace_name, publication_name)
