import uuid
import pytest

from layman import settings, app as app, LaymanError
from layman.map import MAP_TYPE
from test_tools.role_service import ensure_role, delete_role
from . import publications, workspaces, users

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA

userinfo_baseline = {"issuer_id": 'mock_test_publications_test',
                     "claims": {"email": "test@oauth2.org",
                                "preferred_username": 'test_preferred',
                                "name": "test ensure user",
                                "given_name": "test",
                                "family_name": "user",
                                "middle_name": "ensure",
                                }
                     }


def ensure_user(username, sub):
    id_workspace_user = workspaces.ensure_workspace(username)
    userinfo = userinfo_baseline.copy()
    userinfo['sub'] = sub
    users.ensure_user(id_workspace_user, userinfo)


class TestOnlyValidUserNames:
    workspace_name = 'test_only_valid_names_workspace'
    username = 'test_only_valid_names_user'

    @pytest.fixture(scope="class", autouse=True)
    def provide_data(self, request):
        ensure_user(self.username, '10')
        workspaces.ensure_workspace(self.workspace_name)
        yield
        if request.node.session.testsfailed == 0:
            workspaces.delete_workspace(self.workspace_name)
            users.delete_user(self.username)

    @classmethod
    @pytest.mark.parametrize("names", [
        pytest.param({username, workspace_name}, id='username-and-workspace-name'),
        pytest.param({workspace_name, username}, id='workspace-name-and-username'),
        pytest.param({'skaljgdalskfglshfgd'}, id='non-existent-username'),
        pytest.param({'mIxEd'}, id='mixed-case'),
    ])
    def test_raises(cls, names):
        with app.app_context():
            with pytest.raises(LaymanError) as exc_info:
                publications.only_valid_user_names(names)
            assert exc_info.value.code == 43


class TestOnlyValidRoleNames:
    role1 = 'TEST_ONLY_VALID_ROLE_NAMES_ROLE1'
    role2 = 'TEST_ONLY_VALID_ROLE_NAMES_ROLE2'
    role64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ_ABCDEFGHIJKLMNOPQRSTUVWXYZ_ABCDEFGHIJ'
    user = 'TEST_ONLY_VALID_ROLE_NAMES_USER'
    non_existent_role = 'TEST_ONLY_VALID_ROLE_NAMES_NON_EXISTENT_ROLE'

    @pytest.fixture(scope="class", autouse=True)
    def provide_data(self, request):
        roles = [self.role1, self.role2, self.role64]
        for role in roles:
            ensure_role(role)
        ensure_user(self.user, '11')
        yield
        if request.node.session.testsfailed == 0:
            users.delete_user(self.user)
            for role in roles:
                delete_role(role)

    @pytest.mark.parametrize("roles", [
        pytest.param({role1}, id='one-existing-role'),
        pytest.param({role1, role2}, id='two-existing-roles'),
        pytest.param({'EVERYONE'}, id='everyone-role'),
        pytest.param({role64}, id='64-characters'),
    ])
    def test_ok(self, roles):
        publications.only_valid_role_names(roles)

    @pytest.mark.parametrize("roles", [
        pytest.param({non_existent_role}, id='non-existent-role'),
        pytest.param({role1, non_existent_role}, id='non-existent-role-of-two-roles'),
        pytest.param({f'USER_{user}'}, id='internal-user-role'),
        pytest.param({f'INVALID__ROLE'}, id='invalid-role-two-underscores'),
        pytest.param({f'0INVALID_ROLE'}, id='invalid-role-starts-with-number'),
        pytest.param({f'ROLE_ADMINISTRATOR'}, id='ROLE_ADMINISTRATOR'),
        pytest.param({f'ROLE_GROUP_ADMIN'}, id='ROLE_GROUP_ADMIN'),
        pytest.param({f'ROLE_AUTHENTICATED'}, id='ROLE_AUTHENTICATED'),
        pytest.param({f'ROLE_ANONYMOUS'}, id='ROLE_ANONYMOUS'),
        pytest.param({f'ADMIN'}, id='ADMIN'),
        pytest.param({f'ADMIN_GROUP'}, id='ADMIN_GROUP'),
        pytest.param({settings.LAYMAN_GS_ROLE}, id='value-of-LAYMAN_GS_ROLE'),
        pytest.param({'ABCDEFGHIJKLMNOPQRSTUVWXYZ_ABCDEFGHIJKLMNOPQRSTUVWXYZ_ABCDEFGHIJK'}, id='65-characters'),
    ])
    def test_raises(self, roles):
        with pytest.raises(LaymanError) as exc_info:
            publications.only_valid_role_names(roles)
        assert exc_info.value.code == 43


def test_at_least_one_can_write():
    workspace_name = 'test_at_least_one_can_write_workspace'
    username = 'test_at_least_one_can_write_user'

    publications.at_least_one_can_write({username}, set())
    publications.at_least_one_can_write(set(), {settings.RIGHTS_EVERYONE_ROLE})
    publications.at_least_one_can_write({username}, set())
    publications.at_least_one_can_write({workspace_name}, set())
    publications.at_least_one_can_write({'lusfjdiaurghalskug'}, set())

    with pytest.raises(LaymanError) as exc_info:
        publications.at_least_one_can_write(set(), set())
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.at_least_one_can_write(set(), {'ROLE1'})
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
    publications.who_can_write_can_read({'ROLE1'}, {'ROLE1'})
    publications.who_can_write_can_read({settings.RIGHTS_EVERYONE_ROLE}, {'ROLE1'})

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
        publications.who_can_write_can_read({username}, {settings.RIGHTS_EVERYONE_ROLE, })
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.who_can_write_can_read({username}, {workspace_name, })
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.who_can_write_can_read({username}, {'ROLE1'})
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.who_can_write_can_read({'ROLE2'}, {'ROLE1'})
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.who_can_write_can_read({'ROLE2'}, {settings.RIGHTS_EVERYONE_ROLE})
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

    with pytest.raises(LaymanError) as exc_info:
        publications.i_can_still_write(username, {'ROLE1'})
    assert exc_info.value.code == 43


class TestOwnerCanStillWrite:
    username = 'test_owner_can_still_write_user'
    username2 = 'test_owner_can_still_write_user2'
    role1 = 'ROLE1'

    @classmethod
    @pytest.mark.parametrize("owner, can_write", [
        pytest.param(None, set(), id='no-owner-empty-rights'),
        pytest.param(None, {settings.RIGHTS_EVERYONE_ROLE}, id='no-owner-rights-everyone'),
        pytest.param(None, {username}, id='no-owner-rights-user'),
        pytest.param(username, {settings.RIGHTS_EVERYONE_ROLE}, id='owner-rights-everyone'),
        pytest.param(username, {username}, id='owner-rights-owner'),
        pytest.param(username, {username, username2}, id='owner-rights-owner-and-other-user'),
        pytest.param(username, {username, role1}, id='owner-rights-owner-and-role'),
    ])
    def test_ok(cls, owner, can_write):
        publications.owner_can_still_write(owner, can_write)

    @classmethod
    @pytest.mark.parametrize("owner, can_write", [
        pytest.param(username, set(), id='owner-empty-rights'),
        pytest.param(username, {username2}, id='owner-rights-other-user'),
        pytest.param(username, {role1}, id='owner-rights-role'),
    ])
    def test_raises(cls, owner, can_write):
        with pytest.raises(LaymanError) as exc_info:
            publications.owner_can_still_write(owner, can_write)
        assert exc_info.value.code == 43


def test_get_user_and_role_names_for_db():
    workspace_name = 'test_get_user_and_role_names_for_db_workspace'
    username = 'test_get_user_and_role_names_for_db_user'

    with app.app_context():
        workspaces.ensure_workspace(workspace_name)
        ensure_user(username, '20')

        user_names, role_names = publications.get_user_and_role_names_for_db({username, }, workspace_name)
        assert user_names == {username}
        assert role_names == set()

        user_names, role_names = publications.get_user_and_role_names_for_db({username, workspace_name, }, workspace_name)
        assert user_names == {username, workspace_name}
        assert role_names == set()

        user_names, role_names = publications.get_user_and_role_names_for_db({username, }, username)
        assert user_names == set()
        assert role_names == set()

        user_names, role_names = publications.get_user_and_role_names_for_db({username, workspace_name, }, username)
        assert user_names == {workspace_name}
        assert role_names == set()

        user_names, role_names = publications.get_user_and_role_names_for_db({username, settings.RIGHTS_EVERYONE_ROLE, }, workspace_name)
        assert user_names == {username}
        assert role_names == set()

        user_names, role_names = publications.get_user_and_role_names_for_db({username, settings.RIGHTS_EVERYONE_ROLE, }, username)
        assert user_names == set()
        assert role_names == set()

        user_names, role_names = publications.get_user_and_role_names_for_db({workspace_name, settings.RIGHTS_EVERYONE_ROLE, 'ROLE1'}, username)
        assert user_names == {workspace_name}
        assert role_names == {'ROLE1'}

        users.delete_user(username)
        workspaces.delete_workspace(workspace_name)


def assert_access_rights(workspace_name,
                         publication_name,
                         publication_type,
                         exp_read_rights,
                         exp_write_rights):
    pubs = publications.get_publication_infos(workspace_name, publication_type)
    assert pubs[(workspace_name, publication_type, publication_name)]["access_rights"]["read"] == exp_read_rights
    assert pubs[(workspace_name, publication_type, publication_name)]["access_rights"]["write"] == exp_write_rights


class TestInsertRights:
    workspace_name = 'test_insert_rights_workspace'
    username = 'test_insert_rights_user'
    username2 = 'test_insert_rights_user2'
    role1 = 'TEST_INSERT_RIGHTS_ROLE1'

    publication_name = 'test_insert_rights_publication_name'
    publication_type = MAP_TYPE

    publication_info = {"name": publication_name,
                        "title": publication_name,
                        "actor_name": username,
                        "publ_type_name": publication_type,
                        "uuid": uuid.uuid4(),
                        }

    @pytest.fixture(scope="function", autouse=True)
    def provide_data(self, request):
        with app.app_context():
            workspaces.ensure_workspace(self.workspace_name)
            ensure_user(self.username, '30')
            ensure_user(self.username2, '40')
            ensure_role(self.role1)
        yield
        if request.node.session.testsfailed == 0:
            with app.app_context():
                delete_role(self.role1)
                users.delete_user(self.username)
                users.delete_user(self.username2)
                workspaces.delete_workspace(self.workspace_name)

    @pytest.mark.parametrize("username, access_rights, exp_read_rights, exp_write_rights", [
        pytest.param(
            username,
            {"read": {username, },
             "write": {username, }, },
            [username, ], [username, ],
            id='personal_only_owner',
        ),
        pytest.param(
            username,
            {"read": {settings.RIGHTS_EVERYONE_ROLE, },
             "write": {settings.RIGHTS_EVERYONE_ROLE, },
             },
            [username, settings.RIGHTS_EVERYONE_ROLE, ], [username, settings.RIGHTS_EVERYONE_ROLE, ],
            id='personal_everyone',
        ),
        pytest.param(
            username,
            {"read": {settings.RIGHTS_EVERYONE_ROLE, username, },
             "write": {settings.RIGHTS_EVERYONE_ROLE, username, },
             },
            [username, settings.RIGHTS_EVERYONE_ROLE, ], [username, settings.RIGHTS_EVERYONE_ROLE, ],
            id='personal_everyone_owner',
        ),
        pytest.param(
            username,
            {"read": {username, username2, },
             "write": {username, username2, },
             },
            [username, username2, ], [username, username2, ],
            id='personal_owner_editor',
        ),
        pytest.param(
            username,
            {"read": {username, username2, role1, },
             "write": {username, username2, role1, },
             },
            [username, role1, username2, ], [username, role1, username2, ],
            id='personal_owner_editor_role',
        ),
        pytest.param(
            workspace_name,
            {"read": {settings.RIGHTS_EVERYONE_ROLE, username, },
             "write": {settings.RIGHTS_EVERYONE_ROLE, username, },
             },
            [username, settings.RIGHTS_EVERYONE_ROLE, ], [username, settings.RIGHTS_EVERYONE_ROLE, ],
            id='public_writer_everyone',
        ),
        pytest.param(
            workspace_name,
            {"read": {settings.RIGHTS_EVERYONE_ROLE, },
             "write": {settings.RIGHTS_EVERYONE_ROLE, },
             },
            [settings.RIGHTS_EVERYONE_ROLE, ], [settings.RIGHTS_EVERYONE_ROLE, ],
            id='public_everyone',
        ),
        pytest.param(
            workspace_name,
            {"read": {settings.RIGHTS_EVERYONE_ROLE, role1, },
             "write": {settings.RIGHTS_EVERYONE_ROLE, role1, },
             },
            [role1, settings.RIGHTS_EVERYONE_ROLE, ], [role1, settings.RIGHTS_EVERYONE_ROLE, ],
            id='public_everyone_role',
        ),
        pytest.param(
            username,
            {"read": {username, username2, role1},
             "write": {username, role1},
             },
            [username, role1, username2], [username, role1],
            id='different_read_and_write',
        ),
    ])
    def test_rights(self, username, access_rights, exp_read_rights, exp_write_rights, ):
        publication_info = self.publication_info.copy()
        publication_info.update({"access_rights": access_rights})
        if users.get_user_infos(username):
            publication_info.update({"actor_name": username})
        publication_info['image_mosaic'] = False
        publications.insert_publication(username, publication_info)
        assert_access_rights(username,
                             self.publication_info["name"],
                             self.publication_info["publ_type_name"],
                             exp_read_rights,
                             exp_write_rights,
                             )
        publications.delete_publication(username, publication_info["publ_type_name"], publication_info["name"])


class TestUpdateRights:
    workspace_name = 'test_update_rights_workspace'
    username = 'test_update_rights_user'
    username2 = 'test_update_rights_user2'
    role1 = 'TEST_UPDATE_RIGHTS_ROLE1'
    role2 = 'TEST_UPDATE_RIGHTS_ROLE2'

    publication_name = 'test_update_rights_publication_name'
    publication_type = MAP_TYPE
    publication_insert_info = {"name": publication_name,
                               "title": publication_name,
                               "publ_type_name": publication_type,
                               "actor_name": username,
                               "uuid": uuid.uuid4(),
                               "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, role1, },
                                                 "write": {settings.RIGHTS_EVERYONE_ROLE, role1, },
                                                 },
                               "image_mosaic": False,
                               }

    @pytest.fixture(scope="function", autouse=True)
    def provide_data(self, request):
        with app.app_context():
            workspaces.ensure_workspace(self.workspace_name)
            ensure_user(self.username, '50')
            ensure_user(self.username2, '60')
            ensure_role(self.role1)
            ensure_role(self.role2)
            publications.insert_publication(self.username, self.publication_insert_info)
        yield
        if request.node.session.testsfailed == 0:
            with app.app_context():
                publications.delete_publication(self.username, self.publication_insert_info["publ_type_name"],
                                                self.publication_insert_info["name"])
                delete_role(self.role1)
                delete_role(self.role2)
                users.delete_user(self.username)
                users.delete_user(self.username2)
                workspaces.delete_workspace(self.workspace_name)

    @pytest.mark.parametrize("username, publication_update_info, exp_read_rights, exp_write_rights", [
        pytest.param(
            username,
            {"access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                               "write": {settings.RIGHTS_EVERYONE_ROLE, }},
             "actor_name": username},
            [username, settings.RIGHTS_EVERYONE_ROLE, ], [username, settings.RIGHTS_EVERYONE_ROLE, ],
            id='personal_everyone',
        ),
        pytest.param(
            username,
            {"access_rights": {"read": {username, username2, },
                               "write": {username, username2, }},
             "actor_name": username},
            [username, username2, ], [username, username2, ],
            id='personal_owner_editor',
        ),
        pytest.param(
            username,
            {"access_rights": {"read": {username, },
                               "write": {username, }},
             "actor_name": username},
            [username, ], [username, ],
            id='personal_owner',
        ),
        pytest.param(
            username,
            {"access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                               "write": {settings.RIGHTS_EVERYONE_ROLE, }},
             "actor_name": None},
            [username, settings.RIGHTS_EVERYONE_ROLE, ], [username, settings.RIGHTS_EVERYONE_ROLE, ],
            id='personal_everyone_as_anonym',
        ),
        pytest.param(
            username,
            {"access_rights": {"read": {username, role2, },
                               "write": {username, role2, }},
             "actor_name": username},
            [username, role2, ], [username, role2, ],
            id='personal_owner_role',
        ),
        pytest.param(
            username,
            {"access_rights": {"read": {username, role2},
                               "write": {username}},
             "actor_name": username},
            [username, role2], [username],
            id='different_read_and_write',
        ),
        pytest.param(
            username,
            {"access_rights": {"write": {settings.RIGHTS_EVERYONE_ROLE, username}},
             "actor_name": None},
            [username, role1, settings.RIGHTS_EVERYONE_ROLE], [username, settings.RIGHTS_EVERYONE_ROLE],
            id='change_write_only',
        ),
    ])
    def test_rights(self, username, publication_update_info, exp_read_rights, exp_write_rights, ):
        publication_info_original = self.publication_insert_info
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
                             exp_read_rights,
                             exp_write_rights,
                             )

    @pytest.mark.parametrize("username, pre_publication_update_info, publication_update_info", [
        pytest.param(
            username,
            {},
            {"access_rights": {"read": {username2, },
                               "write": {username2, },
                               },
             'actor_name': username2},
            id='personal_without_owner',
        ),
        pytest.param(
            username,
            {},
            {"access_rights": {"read": {username, },
                               },
             'actor_name': username},
            id='personal_remove_editor_reading',
        ),
        pytest.param(
            username,
            {"access_rights": {"read": {username, },
                               "write": {username, },
                               },
             'actor_name': username},
            {"access_rights": {"write": {username, username2, },
                               },
             'actor_name': username},
            id='personal_add_only_writer',
        ),
        pytest.param(
            username,
            {"access_rights": {"read": {username, },
                               "write": {username, },
                               },
             'actor_name': username},
            {"access_rights": {"write": {settings.RIGHTS_EVERYONE_ROLE, },
                               },
             'actor_name': username},
            id='personal_write_everyone',
        ),
    ])
    def test_validation(self, username, pre_publication_update_info, publication_update_info):
        publication_info_original = self.publication_insert_info
        if pre_publication_update_info:
            pre_publication_update_info["publ_type_name"] = publication_info_original["publ_type_name"]
            pre_publication_update_info["name"] = publication_info_original["name"]
            publications.update_publication(username,
                                            pre_publication_update_info,
                                            )
        if not publication_update_info.get("publ_type_name"):
            publication_update_info["publ_type_name"] = publication_info_original["publ_type_name"]
        if not publication_update_info.get("name"):
            publication_update_info["name"] = publication_info_original["name"]
        with pytest.raises(LaymanError) as exc_info:
            publications.update_publication(username,
                                            publication_update_info,
                                            )
        assert exc_info.value.code == 43
