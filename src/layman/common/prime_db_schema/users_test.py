from layman import settings, app as app
from . import users as user_util, workspaces as workspace_util

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def test_get_user_infos():
    with app.app_context():
        user_util.get_user_infos()
        user_util.get_user_infos('test2')
        user_util.get_user_infos('asůldghwíeghsdlkfj')


def test_ensure_user():
    username = 'test_ensure_user'
    userinfo = {"iss_id": 'mock_test',
                "sub": '1',
                "claims": {"email": "test@liferay.com",
                           "name": "test ensure user",
                           "preferred_username": 'test_preferred',
                           "given_name": "test",
                           "family_name": "user",
                           "middle_name": "ensure",
                           }
                }
    with app.app_context():
        id_workspace = workspace_util.ensure_workspace(username)
        user_id = user_util.ensure_user(id_workspace, userinfo)
        assert user_id
        user_id2 = user_util.ensure_user(id_workspace, userinfo)
        assert user_id2 == user_id


def test_delete_user():
    user = 'test_delete_user_user'
    workspace = 'test_delete_user_workspace'
    userinfo = {"iss_id": 'mock_test',
                "sub": '1',
                "claims": {"email": "test@liferay.com",
                           "preferred_username": 'test_preferred',
                           "name": "test ensure user",
                           "given_name": "test",
                           "family_name": "user",
                           "middle_name": "ensure",
                           }
                }

    with app.app_context():
        id_user_workspace = workspace_util.ensure_workspace(user)
        user_util.ensure_user(id_user_workspace, userinfo)

        workspace_util.ensure_workspace(workspace)

        user_util.delete_user(user)
        assert not user_util.get_user_infos(user)
        assert not workspace_util.get_workspace_infos(user)

        user_util.delete_user(workspace)
        assert not user_util.get_user_infos(workspace)
        assert workspace_util.get_workspace_infos(workspace)
