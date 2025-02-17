import os
import pathlib
import glob

from lxml import etree
from werkzeug.datastructures import FileStorage

from layman import patch_mode, LaymanError, layer
from layman.common import empty_method, empty_method_returns_dict
from . import util
from . import input_file

LAYER_SUBDIR = __name__.rsplit('.', maxsplit=1)[-1]

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT

pre_publication_action_check = empty_method
post_layer = empty_method
patch_layer = empty_method
get_metadata_comparison = empty_method_returns_dict


def get_layer_input_style_dir(workspace, layername):
    input_style_dir = os.path.join(util.get_layer_dir(workspace, layername),
                                   LAYER_SUBDIR)
    return input_style_dir


def ensure_layer_input_style_dir(workspace, layername):
    input_style_dir = get_layer_input_style_dir(workspace, layername)
    pathlib.Path(input_style_dir).mkdir(parents=True, exist_ok=True)
    return input_style_dir


get_layer_info = input_file.get_layer_info


def delete_layer(workspace, layername):
    util.delete_layer_subdir(workspace, layername, LAYER_SUBDIR)


def get_file_path(workspace, layername, with_extension=True):
    input_style_dir = get_layer_input_style_dir(workspace, layername)
    style_files = glob.glob(os.path.join(input_style_dir, layername + '.*'))
    if with_extension:
        result = style_files[0] if style_files else None
    else:
        result = os.path.join(input_style_dir, layername)
    return result


def save_layer_file(workspace, layername, style_file, style_type):
    delete_layer(workspace, layername)
    if style_file:
        style_path_clear = get_file_path(workspace, layername, with_extension=False)
        style_path = style_path_clear + '.' + style_type.extension
        ensure_layer_input_style_dir(workspace, layername)
        if isinstance(style_file, FileStorage):
            style_file.save(style_path)
        else:
            with open(style_path, 'wb') as out:
                out.write(style_file.read())


def get_layer_file(workspace, layername):
    style_path = get_file_path(workspace, layername)

    if style_path and os.path.exists(style_path):
        return open(style_path, 'rb')
    return None


def get_style_type_from_file_storage(file_storage):
    if file_storage:
        try:
            xml = file_storage.read()
            file_storage.seek(0)
            xml_tree = etree.fromstring(xml)
            root_tag = xml_tree.tag
            root_attribute = etree.QName(root_tag).localname
            result = next((sd for sd in layer.STYLE_TYPES_DEF if sd.root_element == root_attribute), None)
            if not result:
                raise LaymanError(46, {
                    'message': f"Unknown root element.",
                    'expected': f"Root element is one of {[sd.root_element for sd in layer.STYLE_TYPES_DEF if sd.root_element]}",
                })
        except etree.XMLSyntaxError as exc:
            raise LaymanError(46, "Unable to parse style file.",) from exc
    else:
        result = layer.NO_STYLE_DEF
    return result
