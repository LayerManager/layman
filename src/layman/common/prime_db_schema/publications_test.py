import pytest
import uuid

from test import process, process_client

from layman import settings, app as app, LaymanError
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE
from . import publications, workspaces, users

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


def test_clear_roles():
    workspace_name = 'test_clear_roles_workspace'
    username = 'test_clear_roles_user'

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

        publications.delete_publication(username, publication_insert_info["publ_type_name"], publication_insert_info["name"])


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
def test_rights_by_rest():
    def test_by_type(prefix,
                     publication_type,
                     publish_method,
                     patch_method,
                     delete_method):
        workspace_name = prefix + '_workspace'
        username = prefix + '_user'
        username2 = prefix + '_user2'
        publication_name = prefix + '_publication'

        with app.app_context():
            workspaces.ensure_workspace(workspace_name)
            id_workspace_user = workspaces.ensure_workspace(username)
            users.ensure_user(id_workspace_user, userinfo)
            id_workspace_user2 = workspaces.ensure_workspace(username2)
            users.ensure_user(id_workspace_user2, userinfo)

            publish_method(workspace_name,
                           publication_name,
                           access_rights={'read': f'{settings.RIGHTS_EVERYONE_ROLE}, {username2}',
                                          'write': f'{settings.RIGHTS_EVERYONE_ROLE}, {username2}'})
            info = publications.get_publication_infos(workspace_name, publication_type)[
                (workspace_name, publication_type, publication_name)]
            assert info['access_rights']['read'] == [username2, settings.RIGHTS_EVERYONE_ROLE]
            assert info['access_rights']['write'] == [username2, settings.RIGHTS_EVERYONE_ROLE]

            patch_method(workspace_name,
                         publication_name,
                         access_rights={'read': f'{settings.RIGHTS_EVERYONE_ROLE}'})
            info = publications.get_publication_infos(workspace_name, publication_type)[
                (workspace_name, publication_type, publication_name)]
            assert info['access_rights']['read'] == [settings.RIGHTS_EVERYONE_ROLE]
            assert info['access_rights']['write'] == [username2, settings.RIGHTS_EVERYONE_ROLE]

            patch_method(workspace_name,
                         publication_name,
                         access_rights={'write': f'{settings.RIGHTS_EVERYONE_ROLE}'})
            info = publications.get_publication_infos(workspace_name, publication_type)[
                (workspace_name, publication_type, publication_name)]
            assert info['access_rights']['read'] == [settings.RIGHTS_EVERYONE_ROLE]
            assert info['access_rights']['write'] == [settings.RIGHTS_EVERYONE_ROLE]

            patch_method(workspace_name,
                         publication_name,
                         access_rights={'read': f'{settings.RIGHTS_EVERYONE_ROLE}, {username}',
                                        'write': f'{settings.RIGHTS_EVERYONE_ROLE}, {username}'})
            info = publications.get_publication_infos(workspace_name, publication_type)[
                (workspace_name, publication_type, publication_name)]
            assert info['access_rights']['read'] == [username, settings.RIGHTS_EVERYONE_ROLE]
            assert info['access_rights']['write'] == [username, settings.RIGHTS_EVERYONE_ROLE]

            delete_method(workspace_name, publication_name)

    test_by_type('test_rest_layer_rights',
                 LAYER_TYPE,
                 process_client.publish_layer,
                 process_client.patch_layer,
                 process_client.delete_layer,
                 )
    test_by_type('test_rest_map_rights',
                 MAP_TYPE,
                 process_client.publish_map,
                 process_client.patch_map,
                 process_client.delete_map,
                 )
