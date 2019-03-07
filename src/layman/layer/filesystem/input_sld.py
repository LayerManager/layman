import os
import pathlib
import shutil

from werkzeug.datastructures import FileStorage

from . import get_layer_dir
from layman.settings import *


def get_layer_input_sld_dir(username, layername):
    input_sld_dir = os.path.join(get_layer_dir(username, layername),
                                 'input_sld')
    return input_sld_dir


def ensure_layer_input_sld_dir(username, layername):
    input_sld_dir = get_layer_input_sld_dir(username, layername)
    pathlib.Path(input_sld_dir).mkdir(parents=True, exist_ok=True)
    return input_sld_dir


def get_layer_info(username, layername):
    if os.path.exists(get_file_path(username, layername)):
        return {
            'name': layername
        }
    else:
        return {}


def update_layer(username, layername, layerinfo):
    pass


def delete_layer(username, layername):
    try:
        shutil.rmtree(get_layer_input_sld_dir(username, layername))
    except FileNotFoundError:
        pass
    layerdir = get_layer_dir(username, layername)
    if os.path.exists(layerdir) and not os.listdir(layerdir):
        os.rmdir(layerdir)
    return {}


def get_file_path(username, layername):
    input_sld_dir = get_layer_input_sld_dir(username, layername)
    return os.path.join(input_sld_dir, layername+'.sld')


def get_layer_names(username):
    # covered by input_files.get_layer_names
    return []


def save_layer_file(username, layername, sld_file):
    sld_path = get_file_path(username, layername)
    if sld_file is None:
        delete_layer(username, layername)
    elif isinstance(sld_file, FileStorage):
        ensure_layer_input_sld_dir(username, layername)
        sld_file.save(sld_path)
    else:
        ensure_layer_input_sld_dir(username, layername)
        with open(sld_path, 'wb') as out:
            out.write(sld_file.read())


def get_layer_file(username, layername):
    sld_path = get_file_path(username, layername)

    if os.path.exists(sld_path):
        return open(sld_path, 'rb')
    return None
