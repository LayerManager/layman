import pytest
import uuid

from test import process, process_client

from layman import settings, app as app, LaymanError
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE
from . import publications, workspaces, users

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
ensure_layman = process.ensure_layman

userinfo_baseline = {"issuer_id": 'mock_test_publications_test',
                     "claims": {"email": "test@liferay.com",
                                "preferred_username": 'test_preferred',
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
                       "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                         "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                         }
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
                       "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                         "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                         }
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
                       "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                         "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                         }
                       }
            publications.update_publication(username, db_info)
            pubs = publications.get_publication_infos(username, publication_type)
            assert pubs[(username, publication_type, publication_name)].get('name') == publication_name
            assert pubs[(username, publication_type, publication_name)].get('title') == publication_title
            assert pubs[(username, publication_type, publication_name)].get('uuid') == uuid_str

            publications.delete_publication(username, publication_type, publication_name)
            pubs = publications.get_publication_infos(username, publication_type)
            assert pubs.get((username, publication_type, publication_name)) is None

            workspaces.delete_workspace(username)

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
        workspaces.delete_workspace(username)


def test_only_valid_names():
    workspace_name = 'test_only_valid_names_workspace'
    username = 'test_only_valid_names_user'

    with app.app_context():
        workspaces.ensure_workspace(workspace_name)
        id_workspace_user = workspaces.ensure_workspace(username)
        userinfo = userinfo_baseline.copy()
        userinfo['sub'] = '10'
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

        users.delete_user(username)
        workspaces.delete_workspace(workspace_name)


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

    with app.app_context():
        workspaces.ensure_workspace(workspace_name)
        id_workspace_user = workspaces.ensure_workspace(username)
        userinfo = userinfo_baseline.copy()
        userinfo['sub'] = '20'
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

        users.delete_user(username)
        workspaces.delete_workspace(workspace_name)


def assert_access_rights(workspace_name,
                         publication_name,
                         publication_type,
                         read_to_test,
                         write_to_test):
    pubs = publications.get_publication_infos(workspace_name, publication_type)
    assert pubs[(workspace_name, publication_type, publication_name)]["access_rights"]["read"] == read_to_test
    assert pubs[(workspace_name, publication_type, publication_name)]["access_rights"]["write"] == write_to_test


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
        publications.delete_publication(username, publication_info["publ_type_name"], publication_info["name"])

    workspace_name = 'test_insert_rights_workspace'
    username = 'test_insert_rights_user'
    username2 = 'test_insert_rights_user2'

    publication_name = 'test_insert_rights_publication_name'
    publication_type = MAP_TYPE

    with app.app_context():
        workspaces.ensure_workspace(workspace_name)
        id_workspace_user = workspaces.ensure_workspace(username)
        userinfo = userinfo_baseline.copy()
        userinfo['sub'] = '30'
        users.ensure_user(id_workspace_user, userinfo)
        id_workspace_user2 = workspaces.ensure_workspace(username2)
        userinfo = userinfo_baseline.copy()
        userinfo['sub'] = '40'
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
                                [username, ],
                                [username, ],
                                )

        case_test_insert_rights(username,
                                publication_info,
                                {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                 "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                 },
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        case_test_insert_rights(username,
                                publication_info,
                                {"read": {settings.RIGHTS_EVERYONE_ROLE, username, },
                                 "write": {settings.RIGHTS_EVERYONE_ROLE, username, },
                                 },
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        case_test_insert_rights(username,
                                publication_info,
                                {"read": {username, username2, },
                                 "write": {username, username2, },
                                 },
                                [username, username2, ],
                                [username, username2, ],
                                )

        case_test_insert_rights(workspace_name,
                                publication_info,
                                {"read": {settings.RIGHTS_EVERYONE_ROLE, username, },
                                 "write": {settings.RIGHTS_EVERYONE_ROLE, username, },
                                 },
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        case_test_insert_rights(workspace_name,
                                publication_info,
                                {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                 "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                 },
                                [settings.RIGHTS_EVERYONE_ROLE, ],
                                [settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        users.delete_user(username)
        users.delete_user(username2)
        workspaces.delete_workspace(workspace_name)


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
        userinfo = userinfo_baseline.copy()
        userinfo['sub'] = '50'
        users.ensure_user(id_workspace_user, userinfo)
        id_workspace_user2 = workspaces.ensure_workspace(username2)
        userinfo = userinfo_baseline.copy()
        userinfo['sub'] = '60'
        users.ensure_user(id_workspace_user2, userinfo)

        publications.insert_publication(username, publication_insert_info)

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   },
                                 'actor_name': username},
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {username, username2, },
                                                   "write": {username, username2, },
                                                   },
                                 'actor_name': username},
                                [username, username2, ],
                                [username, username2, ],
                                )

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   },
                                 'actor_name': username},
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {username, },
                                                   "write": {username, },
                                                   },
                                 'actor_name': username},
                                [username, ],
                                [username, ],
                                )

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   },
                                 'actor_name': None},
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"read": {username2, },
                                                       "write": {username2, },
                                                       },
                                     'actor_name': username2},
                                    [username, username2, ],
                                    [username, username2, ],
                                    )
            assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"read": {username, },
                                                       },
                                     'actor_name': username},
                                    [username, username2, ],
                                    [username, username2, ],
                                    )
            assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"read": {username, },
                                                       },
                                     'actor_name': username},
                                    [username, username2, ],
                                    [username, username2, ],
                                    )
            assert exc_info.value.code == 43

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {username, },
                                                   "write": {username, },
                                                   },
                                 'actor_name': username},
                                [username, ],
                                [username, ],
                                )
        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"write": {username, username2, },
                                                       },
                                     'actor_name': username},
                                    [username, username2, ],
                                    [username, username2, username2, ],
                                    )
            assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"write": {settings.RIGHTS_EVERYONE_ROLE, },
                                                       },
                                     'actor_name': username},
                                    [username, username2, ],
                                    [settings.RIGHTS_EVERYONE_ROLE, ],
                                    )
            assert exc_info.value.code == 43

        publications.delete_publication(username, publication_insert_info["publ_type_name"], publication_insert_info["name"])
        users.delete_user(username)
        users.delete_user(username2)
        workspaces.delete_workspace(workspace_name)


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
