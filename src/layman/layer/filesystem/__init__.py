import os
from . import util


def get_usernames():
    usersdir = util.get_users_dir()
    if not os.path.exists(usersdir):
        return []
    user_names = [
        subfile for subfile in os.listdir(usersdir)
        if os.path.isdir(os.path.join(usersdir, subfile))
    ]
    return user_names


def check_username(username):
    pass


def check_new_layername(username, layername):
    pass