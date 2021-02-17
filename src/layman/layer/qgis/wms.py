import os

from . import util, wms
from .. import db
from layman import patch_mode, settings
from layman.layer import qgis, util as layer_util
from layman.layer.filesystem import input_style

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT
VERSION = "1.3.0"


def get_publication_uuid(username, publication_type, publication_name):
    return None


def get_metadata_comparison(username, layername):
    pass


def pre_publication_action_check(username, layername):
    pass


def get_layer_info(username, layername):
    input_file_dir = qgis.get_layer_dir(username, layername)
    result = {}
    if os.path.exists(input_file_dir):
        result = {'name': layername}
    return result


def post_layer(username, layername):
    pass


def patch_layer(username, layername):
    pass


def delete_layer(username, layername):
    style_stream = util.get_layer_style_stream(username, layername)
    if style_stream:
        result = {
            'style': {
                'file': style_stream,
            }
        }
    else:
        result = {}
    qgis.delete_layer_dir(username, layername)
    return result


def get_layer_capabilities_url(workspace, layer):
    url = f'{settings.LAYMAN_QGIS_URL}?SERVICE=WMS&REQUEST=GetCapabilities&VERSION={VERSION}&map={get_layer_file_path(workspace, layer)}'
    return url


def get_layer_file_path(workspace, layer):
    return os.path.join(qgis.get_layer_dir(workspace, layer), f'{layer}.qgis')


def save_qgs_file(workspace, layer):
    info = layer_util.get_layer_info(workspace, layer)
    uuid = info['uuid']
    qgis.ensure_layer_dir(workspace, layer)
    layer_bbox = db.get_bbox(workspace, layer)
    layer_bbox = layer_bbox or settings.LAYMAN_DEFAULT_OUTPUT_BBOX
    qml_path = input_style.get_file_path(workspace, layer)
    layer_qml = util.fill_layer_template(workspace, layer, uuid, layer_bbox, qml_path)
    qgs_str = util.fill_project_template(workspace, layer, uuid, layer_qml, settings.LAYMAN_OUTPUT_SRS_LIST, layer_bbox)
    with open(wms.get_layer_file_path(workspace, layer), "w") as qgs_file:
        print(qgs_str, file=qgs_file)
