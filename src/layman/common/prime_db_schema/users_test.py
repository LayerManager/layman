from test.flask_client import client

from layman import settings, app as app
from . import users as user_util, workspaces as workspace_util

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def test_get_user_infos(client):
    with app.app_context():
        users = user_util.get_user_infos()
        users = user_util.get_user_infos('test2')
        users = user_util.get_user_infos('asůldghwíeghsdlkfj')


def test_ensure_user(client):
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
