import os
import pathlib
import shutil

from layman import settings
from layman.util import get_publication_types


PUBL_TYPE_DEF_KEY = '.'.join(__name__.split('.')[:-1])


def get_users_dir():
    usersdir = os.path.join(settings.LAYMAN_DATA_DIR, 'users')
    return usersdir


def get_user_dir(username):
    userdir = os.path.join(get_users_dir(), username)
    return userdir


def ensure_user_dir(username):
    userdir = get_user_dir(username)
    pathlib.Path(userdir).mkdir(exist_ok=True, parents=True)
    return userdir


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


