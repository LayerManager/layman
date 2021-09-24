import os
import pathlib
import glob

from lxml import etree
from werkzeug.datastructures import FileStorage

from layman import patch_mode, LaymanError, layer, settings
from layman.common import empty_method, empty_method_returns_dict
from layman.common.filesystem import input_file as common_input_file
from . import util
from . import input_file
from .. import filesystem

LAYER_SUBDIR = __name__.split('.')[-1]

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT

pre_publication_action_check = empty_method
post_layer = empty_method
patch_layer = empty_method
get_metadata_comparison = empty_method_returns_dict

EXTERNAL_IMAGES_XPATHS = {('.//prop[@k="imageFile" or @k="svgFile"]', 'v', ),
                          ('.//Option[@name="imageFile" or @name="svgFile"]', 'value',)}


def get_layer_input_style_dir(workspace, layername):
    input_style_dir = os.path.join(util.get_layer_dir(workspace, layername),
                                   LAYER_SUBDIR)
    return input_style_dir


def ensure_layer_input_style_dir(workspace, layername):
    input_style_dir = get_layer_input_style_dir(workspace, layername)
    pathlib.Path(input_style_dir).mkdir(parents=True, exist_ok=True)
    return input_style_dir


get_publication_uuid = input_file.get_publication_uuid


def get_layer_info(workspace, layername):
    input_style_dir = get_layer_input_style_dir(workspace, layername)
    if os.path.exists(input_style_dir):
        result = {'name': layername}
        external_images_dir = get_external_images_dir(workspace, layername)
        if os.path.exists(external_images_dir):
            result['_style'] = {'external_images_dir': external_images_dir}
    else:
        result = dict()
    return result


def get_external_images_dir(workspace, layername):
    input_style_dir = get_layer_input_style_dir(workspace, layername)
    return os.path.join(input_style_dir, filesystem.EXTERNAL_IMAGES_DIR)


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


def get_mapping_from_external_image_list(external_images):
    return {path: os.path.join(filesystem.EXTERNAL_IMAGES_DIR, f'image_{idx}{os.path.splitext(path)[1]}') for idx, path in
            enumerate(external_images)}


def adjust_qml_external_image_paths(xml_etree, image_mapping):
    for xpath, attr_name in EXTERNAL_IMAGES_XPATHS:
        for element in xml_etree.xpath(xpath):
            original_path = element.attrib[attr_name]
            if original_path in image_mapping:
                element.attrib[attr_name] = f'./{image_mapping[original_path]}'


def save_layer_files(workspace, layername, style_file, style_type, style_files, external_image_paths, ):
    delete_layer(workspace, layername)

    if style_file:
        ensure_layer_input_style_dir(workspace, layername)
        style_path_clear = get_file_path(workspace, layername, with_extension=False)
        style_path = style_path_clear + '.' + style_type.extension

        if isinstance(style_file, FileStorage):
            xml = style_file.read()
            style_file.seek(0)
            xml_tree = etree.fromstring(xml)
        else:
            xml_tree = etree.parse(style_file)

        if external_image_paths:
            external_images = [ext_image for ext_image in style_files if
                               ext_image != style_file and ext_image.filename in external_image_paths]
            if external_images:
                assert style_type.code == 'qml', f'workspace={workspace}, layername={layername}, style_type={style_type}'
                ext_image_mapping = get_mapping_from_external_image_list(external_image_paths)
                input_style_dir = get_layer_input_style_dir(workspace, layername)
                common_input_file.save_files(external_images, ext_image_mapping, prefix=input_style_dir)
                adjust_qml_external_image_paths(xml_tree, ext_image_mapping)

        full_xml_str = etree.tostring(xml_tree, encoding='unicode', pretty_print=True)
        with open(style_path, "w") as opened_style_file:
            print(full_xml_str, file=opened_style_file)


def get_layer_file(workspace, layername):
    style_path = get_file_path(workspace, layername)

    if style_path and os.path.exists(style_path):
        return open(style_path, 'rb')
    return None


def get_style_type_from_file_storage(file_storage):
    if file_storage:
        xml = file_storage.read()
        file_storage.seek(0)
        xml_tree = etree.fromstring(xml)
        root_tag = xml_tree.tag
        root_attribute = etree.QName(root_tag).localname
        result = next((sd for sd in layer.STYLE_TYPES_DEF if sd.root_element == root_attribute), None)
        if not result:
            raise LaymanError(46)
    else:
        result = layer.NO_STYLE_DEF
    return result


def get_external_files_from_qml(qml):
    external_files = set()
    for xpath, attr_name in EXTERNAL_IMAGES_XPATHS:
        part_external_files = qml.xpath(f'{xpath}/@{attr_name}')
        external_files.update(part_external_files)
    return external_files


def get_external_files_from_qml_file(file_path):
    qml = etree.parse(file_path)
    return get_external_files_from_qml(qml)


def get_all_allowed_main_extensions():
    return settings.STYLE_FILE_EXTENSIONS


def get_main_file(filestorages):
    return next((fn for fn in filestorages if os.path.splitext(fn.filename)[1]
                 in get_all_allowed_main_extensions()), None)


def check_file_styles(external_files_from_style, style_files, ):
    style_file_names = [fn.filename for fn in style_files]
    all_main_files = [fn for fn in style_file_names if os.path.splitext(fn)[1]
                      in get_all_allowed_main_extensions()]
    if len(all_main_files) > 1:
        raise LaymanError(52, data={'found_style_files': all_main_files})
    if external_files_from_style:
        missing_files = [file_path for file_path in external_files_from_style if file_path not in style_file_names]
        if missing_files:
            raise LaymanError(53, data={'missing_files': missing_files})
