from layman.http import LaymanError
from layman import settings
from layman.db import users as users_util


def get_usernames():
    return users_util.get_user_infos().keys()


def check_username(username, conn_cur=None):
    if username in settings.PG_NON_USER_SCHEMAS:
        raise LaymanError(35, {'reserved_by': __name__, 'schema': username})


def ensure_whole_user(username):
    users_util.ensure_user(username)


def delete_whole_user(username):
    users_util.delete_user(username)
