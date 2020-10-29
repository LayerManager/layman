from test import process, process_client

from layman import settings, app as app
from . import users as user_util, workspaces as workspace_util

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
ensure_layman = process.ensure_layman


def test_get_user_infos(ensure_layman):
    with app.app_context():
        user_util.get_user_infos()
        user_util.get_user_infos('test2')
        user_util.get_user_infos('asůldghwíeghsdlkfj')


def test_ensure_user(ensure_layman):
    username = 'test_ensure_user'
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
        id_workspace = workspace_util.ensure_workspace(username)
        user_id = user_util.ensure_user(id_workspace, userinfo)
        assert user_id
        user_id2 = user_util.ensure_user(id_workspace, userinfo)
        assert user_id2 == user_id
