from test.flask_client import client

from layman import settings, app as app
from . import users as user_util

DB_SCHEMA = settings.PG_LAYMAN_SCHEMA


def test_get_user_infos(client):
    with app.app_context():
        users = user_util.get_user_infos()
        users = user_util.get_user_infos('test2')
        users = user_util.get_user_infos('asůldghwíeghsdlkfj')


def test_ensure_user(client):
    username = 'test_ensure_user'
    with app.app_context():
        user_id = user_util.ensure_user(username)
        assert user_id
        user_id2 = user_util.ensure_user(username)
        assert user_id2 == user_id
