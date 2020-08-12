import os
import pathlib
import shutil
from flask import current_app

from layman import settings
from layman.util import get_publication_types

PUBL_TYPE_DEF_KEY = '.'.join(__name__.split('.')[:-1])


def get_usernames():
    usersdir = get_users_dir()
    if not os.path.exists(usersdir):
        return []
    user_names = [
        subfile for subfile in os.listdir(usersdir)
        if os.path.isdir(os.path.join(usersdir, subfile))
    ]
    return user_names


def get_users_dir():
    usersdir = os.path.join(settings.LAYMAN_DATA_DIR, 'users')
    return usersdir


def get_user_dir(username):
    userdir = os.path.join(get_users_dir(), username)
    return userdir


# TODO consider renaming
def ensure_user_workspace(username):
    userdir = get_user_dir(username)
    pathlib.Path(userdir).mkdir(exist_ok=True, parents=True)
    return userdir


def delete_user_workspace(username):
    userdir = get_user_dir(username)
    try:
        os.rmdir(userdir)
    except FileNotFoundError:
        pass


def ensure_whole_user(username):
    ensure_user_workspace(username)


def delete_whole_user(username):
    delete_user_workspace(username)


def get_publications_dir(publ_type, username):
    publ_types = get_publication_types()
    dirname = publ_types[publ_type][PUBL_TYPE_DEF_KEY]['publications_dir']
    layersdir = os.path.join(get_user_dir(username), dirname)
    return layersdir


def get_publication_dir(publ_type, username, publ_name):
    publ_dir = os.path.join(
        get_publications_dir(publ_type, username),
        publ_name
    )
    return publ_dir


def ensure_publication_dir(publ_type, username, publ_name):
    publ_dir = get_publication_dir(publ_type, username, publ_name)
    pathlib.Path(publ_dir).mkdir(exist_ok=True, parents=True)
    return publ_dir


def delete_publication_subfile(publ_type, username, publ_name, subfile):
    publ_dir = get_publication_dir(publ_type, username, publ_name)
    publ_subfile = os.path.join(publ_dir, subfile)
    try:
        os.remove(publ_subfile)
    except OSError:
        pass
    if os.path.exists(publ_dir) and not os.listdir(publ_dir):
        os.rmdir(publ_dir)
    return {}


def delete_publication_subdir(publ_type, username, publ_name, subdir):
    publ_dir = get_publication_dir(publ_type, username, publ_name)
    publ_subdir = os.path.join(publ_dir, subdir)
    try:
        shutil.rmtree(publ_subdir)
    except FileNotFoundError:
        pass
    if os.path.exists(publ_dir) and not os.listdir(publ_dir):
        os.rmdir(publ_dir)
    return {}
