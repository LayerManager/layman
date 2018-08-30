import pathlib

from layman.settings import *


def get_user_dir(username):
    userdir = os.path.join(LAYMAN_DATA_PATH, username)
    return userdir


def ensure_user_dir(username):
    userdir = get_user_dir(username)
    pathlib.Path(userdir).mkdir(exist_ok=True)
    return userdir


def check_username(username):
    pass

def check_new_layername(username, layername):
    pass