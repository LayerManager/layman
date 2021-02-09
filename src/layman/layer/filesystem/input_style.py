import os
import pathlib

from lxml import etree as ET
from werkzeug.datastructures import FileStorage

from layman import patch_mode, LaymanError, layer
from . import util
from . import input_file

LAYER_SUBDIR = __name__.split('.')[-1]

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


def get_layer_input_style_dir(username, layername):
    input_style_dir = os.path.join(util.get_layer_dir(username, layername),
                                   LAYER_SUBDIR)
    return input_style_dir


def ensure_layer_input_style_dir(username, layername):
    input_style_dir = get_layer_input_style_dir(username, layername)
    pathlib.Path(input_style_dir).mkdir(parents=True, exist_ok=True)
    return input_style_dir


get_layer_info = input_file.get_layer_info

get_publication_uuid = input_file.get_publication_uuid


def pre_publication_action_check(username, layername):
    pass


def post_layer(username, layername):
    pass


def patch_layer(username, layername):
    pass


def delete_layer(username, layername):
    util.delete_layer_subdir(username, layername, LAYER_SUBDIR)


def get_file_path(username, layername):
    input_style_dir = get_layer_input_style_dir(username, layername)
    return os.path.join(input_style_dir, layername + '.sld')


def save_layer_file(username, layername, style_file):
    style_path = get_file_path(username, layername)
    if style_file is None:
        delete_layer(username, layername)
    elif isinstance(style_file, FileStorage):
        ensure_layer_input_style_dir(username, layername)
        style_file.save(style_path)
    else:
        ensure_layer_input_style_dir(username, layername)
        with open(style_path, 'wb') as out:
            out.write(style_file.read())


def get_layer_file(username, layername):
    style_path = get_file_path(username, layername)

    if os.path.exists(style_path):
        return open(style_path, 'rb')
    return None


def get_metadata_comparison(username, publication_name):
    pass


def get_style_type_from_xml_file(style_path):
    if os.path.exists(style_path):
        xml_tree = etree.parse(style_path)
        root_tag = xml_tree.getroot().tag
        root_attribute = etree.QName(root_tag).localname
        result = next((sd for sd in layer.STYLE_TYPES_DEF if sd.root_element == root_attribute), None)
        if not result:
            raise LaymanError(46)
    else:
        result = layer.NO_STYLE_DEF
    return result


def get_layer_style_type(workspace, layer):
    return get_style_type_from_xml_file(get_file_path(workspace, layer))
