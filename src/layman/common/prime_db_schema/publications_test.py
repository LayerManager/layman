import uuid
from test import process_client
import pytest

from layman import settings, app as app, LaymanError
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE
from . import publications, workspaces, users

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA

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
                             style_type,
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
                       'style_type': style_type,
                       "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                         "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                         },
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
                                         },
                       'style_type': style_type,
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
                                         },
                       'style_type': style_type,
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
                         LAYER_TYPE,
                         'sld',
                         )
    publications_by_type('test_publication_basic_map',
                         MAP_TYPE,
                         None,
                         )


class TestSelectPublicationsBasic:
    workspace1 = 'test_select_publications_basic_workspace1'
    workspace2 = 'test_select_publications_basic_workspace2'
    qml_style_file = 'sample/style/small_layer.qml'
    publications = [(workspace1, LAYER_TYPE, 'test_select_publications_publication1le', dict()),
                    (workspace1, LAYER_TYPE, 'test_select_publications_publication1le_qml', {'style_file': qml_style_file}),
                    (workspace1, MAP_TYPE, 'test_select_publications_publication1me', dict()),
                    (workspace2, LAYER_TYPE, 'test_select_publications_publication2le', dict()),
                    ]

    @pytest.fixture(scope="class")
    def provide_data(self):
        for publication in self.publications:
            process_client.publish_workspace_publication(publication[1], publication[0], publication[2], **publication[3])
        yield
        for publication in self.publications:
            process_client.delete_workspace_publication(publication[1], publication[0], publication[2])

    @staticmethod
    @pytest.mark.parametrize('query_params, expected_publications', [
        ({'workspace_name': workspace1, 'pub_type': LAYER_TYPE},
         [(workspace1, LAYER_TYPE, 'test_select_publications_publication1le'),
          (workspace1, LAYER_TYPE, 'test_select_publications_publication1le_qml'),
          ]),
        ({'workspace_name': workspace1, 'pub_type': MAP_TYPE}, [(workspace1, MAP_TYPE, 'test_select_publications_publication1me'), ]),
        ({'workspace_name': workspace1, 'style_type': 'qml'},
         [(workspace1, LAYER_TYPE, 'test_select_publications_publication1le_qml'), ]),
        ({'workspace_name': workspace1, 'style_type': 'sld'},
         [(workspace1, LAYER_TYPE, 'test_select_publications_publication1le'), ]),
        ({'workspace_name': workspace1}, [(workspace1, LAYER_TYPE, 'test_select_publications_publication1le'),
                                          (workspace1, LAYER_TYPE, 'test_select_publications_publication1le_qml'),
                                          (workspace1, MAP_TYPE, 'test_select_publications_publication1me'),
                                          ]),
        (dict(), [(workspace1, LAYER_TYPE, 'test_select_publications_publication1le'),
                  (workspace1, LAYER_TYPE, 'test_select_publications_publication1le_qml'),
                  (workspace1, MAP_TYPE, 'test_select_publications_publication1me'),
                  (workspace2, LAYER_TYPE, 'test_select_publications_publication2le'),
                  ]),
    ])
    @pytest.mark.usefixtures('ensure_layman', 'provide_data')
    def test_get_publications(query_params, expected_publications):
        with app.app_context():
            infos = publications.get_publication_infos(**query_params)
        info_publications = list(infos.keys())
        assert expected_publications == info_publications


class TestSelectPublicationsComplex:
    workspace1 = 'test_select_publications_complex_workspace1'
    workspace2 = 'test_select_publications_complex_workspace2'
    authn_headers_user1 = process_client.get_authz_headers(workspace1)
    authn_headers_user2 = process_client.get_authz_headers(workspace2)
    publications = [
        (workspace1, MAP_TYPE, 'test_select_publications_publication1e',
         {'headers': authn_headers_user1,
          'title': 'Příliš žluťoučký Kůň úpěl ďábelské ódy',
          'access_rights': {'read': settings.RIGHTS_EVERYONE_ROLE,
                            'write': settings.RIGHTS_EVERYONE_ROLE}, }),
        (workspace1, MAP_TYPE, 'test_select_publications_publication1o',
         {'headers': authn_headers_user1,
          'title': 'Ďůlek kun Karel',
          'access_rights': {'read': workspace1,
                            'write': workspace1}, }),
        (workspace1, MAP_TYPE, 'test_select_publications_publication1oe',
         {'headers': authn_headers_user1,
          'title': 'jedna dva tři čtyři',
          'access_rights': {'read': settings.RIGHTS_EVERYONE_ROLE,
                            'write': workspace1}, }),
        (workspace2, MAP_TYPE, 'test_select_publications_publication2e',
         {'headers': authn_headers_user2,
          'title': 'Svíčky is the best game',
          'access_rights': {'read': settings.RIGHTS_EVERYONE_ROLE,
                            'write': settings.RIGHTS_EVERYONE_ROLE}, }),
        (workspace2, MAP_TYPE, 'test_select_publications_publication2o',
         {'headers': authn_headers_user2,
          'title': 'druhá mapa JeDnA óda',
          'access_rights': {'read': workspace2,
                            'write': workspace2}, }),
    ]

    @pytest.fixture(scope="class")
    def provide_data(self):
        process_client.ensure_reserved_username(self.workspace1, self.authn_headers_user1)
        process_client.ensure_reserved_username(self.workspace2, self.authn_headers_user2)
        for publication in self.publications:
            process_client.publish_workspace_publication(publication[1], publication[0], publication[2], **publication[3])
        yield
        for publication in self.publications:
            process_client.delete_workspace_publication(publication[1], publication[0], publication[2], publication[3].get('headers'))

    @staticmethod
    @pytest.mark.parametrize('query_params, expected_publications', [
        (dict(), [(workspace1, MAP_TYPE, 'test_select_publications_publication1e'),
                  (workspace1, MAP_TYPE, 'test_select_publications_publication1o'),
                  (workspace1, MAP_TYPE, 'test_select_publications_publication1oe'),
                  (workspace2, MAP_TYPE, 'test_select_publications_publication2e'),
                  (workspace2, MAP_TYPE, 'test_select_publications_publication2o'),
                  ]),
        ({'reader': settings.ANONYM_USER}, [(workspace1, MAP_TYPE, 'test_select_publications_publication1e'),
                                            (workspace1, MAP_TYPE, 'test_select_publications_publication1oe'),
                                            (workspace2, MAP_TYPE, 'test_select_publications_publication2e'),
                                            ]),
        ({'reader': workspace2}, [(workspace1, MAP_TYPE, 'test_select_publications_publication1e'),
                                  (workspace1, MAP_TYPE, 'test_select_publications_publication1oe'),
                                  (workspace2, MAP_TYPE, 'test_select_publications_publication2e'),
                                  (workspace2, MAP_TYPE, 'test_select_publications_publication2o'),
                                  ]),
        ({'writer': settings.ANONYM_USER}, [(workspace1, MAP_TYPE, 'test_select_publications_publication1e'),
                                            (workspace2, MAP_TYPE, 'test_select_publications_publication2e'),
                                            ]),
        ({'writer': workspace2}, [(workspace1, MAP_TYPE, 'test_select_publications_publication1e'),
                                  (workspace2, MAP_TYPE, 'test_select_publications_publication2e'),
                                  (workspace2, MAP_TYPE, 'test_select_publications_publication2o'),
                                  ]),
        ({'full_text_filter': 'dva'}, [(workspace1, MAP_TYPE, 'test_select_publications_publication1oe'),
                                       ]),
        ({'full_text_filter': 'games'}, [(workspace2, MAP_TYPE, 'test_select_publications_publication2e'),
                                         ]),
        ({'full_text_filter': 'kun'}, [(workspace1, MAP_TYPE, 'test_select_publications_publication1e'),
                                       (workspace1, MAP_TYPE, 'test_select_publications_publication1o'),
                                       ]),
        ({'full_text_filter': 'jedna'}, [(workspace1, MAP_TYPE, 'test_select_publications_publication1oe'),
                                         (workspace2, MAP_TYPE, 'test_select_publications_publication2o'),
                                         ]),
        ({'full_text_filter': 'upet'}, []),
        ({'full_text_filter': 'dva | kun'}, [(workspace1, MAP_TYPE, 'test_select_publications_publication1e'),
                                             (workspace1, MAP_TYPE, 'test_select_publications_publication1o'),
                                             (workspace1, MAP_TYPE, 'test_select_publications_publication1oe'),
                                             ]),
        ({'full_text_filter': 'kun & ody'}, [(workspace1, MAP_TYPE, 'test_select_publications_publication1e'),
                                             ]),
        ({'order_by_list': ['full_text'], 'ordering_full_text': 'jedna'}, [
            (workspace1, MAP_TYPE, 'test_select_publications_publication1oe'),
            (workspace2, MAP_TYPE, 'test_select_publications_publication2o'),
            (workspace1, MAP_TYPE, 'test_select_publications_publication1e'),
            (workspace1, MAP_TYPE, 'test_select_publications_publication1o'),
            (workspace2, MAP_TYPE, 'test_select_publications_publication2e'),
        ]),
        ({'full_text_filter': 'dva | kun', 'order_by_list': ['full_text'], 'ordering_full_text': 'karel | kun'}, [
            (workspace1, MAP_TYPE, 'test_select_publications_publication1o'),
            (workspace1, MAP_TYPE, 'test_select_publications_publication1e'),
            (workspace1, MAP_TYPE, 'test_select_publications_publication1oe'),
        ]),
        ({'order_by_list': ['title'], }, [
            (workspace2, MAP_TYPE, 'test_select_publications_publication2o'),
            (workspace1, MAP_TYPE, 'test_select_publications_publication1o'),
            (workspace1, MAP_TYPE, 'test_select_publications_publication1oe'),
            (workspace1, MAP_TYPE, 'test_select_publications_publication1e'),
            (workspace2, MAP_TYPE, 'test_select_publications_publication2e'),
        ]),
        ({'order_by_list': ['last_change'], }, [
            (workspace2, MAP_TYPE, 'test_select_publications_publication2o'),
            (workspace2, MAP_TYPE, 'test_select_publications_publication2e'),
            (workspace1, MAP_TYPE, 'test_select_publications_publication1oe'),
            (workspace1, MAP_TYPE, 'test_select_publications_publication1o'),
            (workspace1, MAP_TYPE, 'test_select_publications_publication1e'),
        ]),
    ])
    @pytest.mark.usefixtures('liferay_mock', 'ensure_layman', 'provide_data')
    def test_get_publications(query_params, expected_publications):
        with app.app_context():
            infos = publications.get_publication_infos(**query_params)
        info_publications = list(infos.keys())
        assert set(expected_publications) == set(info_publications)
        assert expected_publications == info_publications


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

    process_client.publish_workspace_layer(username, publ_name)
    process_client.publish_workspace_map(username, publ_name)
    process_client.publish_workspace_layer(username2, publ_name)
    process_client.publish_workspace_map(username2, publ_name)

    with app.app_context():
        pubs = publications.get_publication_infos(username)
        assert len(pubs) == 2
        pubs = publications.get_publication_infos(username2)
        assert len(pubs) == 2
        pubs = publications.get_publication_infos()
        assert len(pubs) >= 4

    process_client.delete_workspace_layer(username, publ_name)
    process_client.delete_workspace_map(username, publ_name)
    process_client.delete_workspace_layer(username2, publ_name)
    process_client.delete_workspace_map(username2, publ_name)
