import os
import glob
from werkzeug.datastructures import FileStorage
from urllib.parse import urljoin

from flask import url_for

from . import get_user_dir
from layman.settings import *


def get_layer_info(username, layername):
    return {}


def update_layer(username, layername, layerinfo):
    pass


def delete_layer(username, layername):
    sld_path = get_file_path(username, layername)
    try:
        os.remove(sld_path)
    except OSError:
        pass
    return {}


def get_file_path(username, layername):
    userdir = get_user_dir(username)
    return os.path.join(userdir, layername+'.sld')


def get_layer_names(username):
    ending = '.sld'
    userdir = get_user_dir(username)
    pattern = os.path.join(userdir, '*'+ending)
    filenames = glob.glob(pattern)
    layer_names = list(map(
        lambda fn: os.path.basename(fn)[:-len(ending)],
        filenames))
    return layer_names


def save_layer_file(username, layername, sld_file):
    sld_path = get_file_path(username, layername)
    if sld_file is None:
        delete_layer(username, layername)
    elif isinstance(sld_file, FileStorage):
        sld_file.save(sld_path)
    else:
        with open(sld_path, 'wb') as out:
            out.write(sld_file.read())


def get_layer_file(username, layername):
    sld_path = get_file_path(username, layername)

    if os.path.exists(sld_path):
        return open(sld_path, 'rb')
    return None
