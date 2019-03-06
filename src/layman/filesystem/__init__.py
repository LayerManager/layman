import pathlib

from layman.settings import *


def get_user_dir(username):
    userdir = os.path.join(LAYMAN_DATA_DIR, 'users', username)
    return userdir


def get_layers_dir(username):
    layersdir = os.path.join(get_user_dir(username), 'layers')
    return layersdir


def get_layer_dir(username, layername):
    layerdir = os.path.join(get_layers_dir(username), layername)
    return layerdir


def ensure_user_dir(username):
    userdir = get_user_dir(username)
    pathlib.Path(userdir).mkdir(exist_ok=True, parents=True)
    return userdir


def ensure_layer_dir(username, layername):
    layerdir = get_layer_dir(username, layername)
    pathlib.Path(layerdir).mkdir(exist_ok=True, parents=True)
    return layerdir


def check_username(username):
    pass

def check_new_layername(username, layername):
    pass