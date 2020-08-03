import os
import pathlib

from werkzeug.datastructures import FileStorage

from layman import patch_mode
from . import util
from . import input_file

LAYER_SUBDIR = __name__.split('.')[-1]

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


def get_layer_input_sld_dir(username, layername):
    input_sld_dir = os.path.join(util.get_layer_dir(username, layername),
                                 LAYER_SUBDIR)
    return input_sld_dir


def ensure_layer_input_sld_dir(username, layername):
    input_sld_dir = get_layer_input_sld_dir(username, layername)
    pathlib.Path(input_sld_dir).mkdir(parents=True, exist_ok=True)
    return input_sld_dir


get_layer_info = input_file.get_layer_info

get_layer_names = input_file.get_layer_names

update_layer = input_file.update_layer

get_publication_names = input_file.get_publication_names

get_publication_uuid = input_file.get_publication_uuid


def delete_layer(username, layername):
    util.delete_layer_subdir(username, layername, LAYER_SUBDIR)


def get_file_path(username, layername):
    input_sld_dir = get_layer_input_sld_dir(username, layername)
    return os.path.join(input_sld_dir, layername + '.sld')


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


def get_metadata_comparison(username, publication_name):
    pass
