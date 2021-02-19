import os
from owslib.wms import WebMapService

from . import util
from layman import patch_mode, settings
from .. import db, qgis, util as layer_util

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
    qml = util.get_style_xml(workspace, layer)
    qml_geometry = util.get_qml_geometry_from_qml(qml)
    db_types = db.get_geometry_types(workspace, layer)
    db_cols = [
        col for col in db.get_all_column_infos(workspace, layer)
        if col.name not in ['wkb_geometry', 'ogc_fid']
    ]
    source_type = util.get_source_type(db_types, qml_geometry)
    layer_qml = util.fill_layer_template(workspace, layer, uuid, layer_bbox, qml, source_type, db_cols)
    qgs_str = util.fill_project_template(workspace, layer, uuid, layer_qml, settings.LAYMAN_OUTPUT_SRS_LIST,
                                         layer_bbox, source_type)
    with open(get_layer_file_path(workspace, layer), "w") as qgs_file:
        print(qgs_str, file=qgs_file)


def wms_direct(wms_url, xml=None, version=None, headers=None):
    version = version or VERSION
    result_wms = WebMapService(wms_url, xml=xml.encode('utf-8') if xml is not None else xml, version=version, headers=headers)
    return result_wms


def get_wms_capabilities(workspace=None, layer=None, headers=None):
    wms_url = get_layer_capabilities_url(workspace, layer)
    return wms_direct(wms_url, headers=headers)
