import os
from owslib.wms import WebMapService

import crs as crs_def
from layman import patch_mode, settings, util as layman_util
from layman.common import bbox as bbox_util, empty_method, empty_method_returns_none, empty_method_returns_dict
from . import util
from .. import db, qgis, util as layer_util

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT
VERSION = "1.1.1"

get_metadata_comparison = empty_method_returns_dict
pre_publication_action_check = empty_method
post_layer = empty_method
patch_layer = empty_method
get_publication_uuid = empty_method_returns_none


def get_layer_info(workspace, layername):
    input_file_dir = qgis.get_layer_dir(workspace, layername)
    result = {}
    if os.path.exists(input_file_dir):
        url = layman_util.url_for('rest_workspace_layer_style.get', workspace=workspace, layername=layername)
        result = {
            'name': layername,
            'style': {
                'url': url,
                'type': 'qml',
            },
            '_wms': {
                'qgis_capabilities_url': get_layer_capabilities_url(workspace, layername),
            }
        }
    return result


def delete_layer(workspace, layername):
    style_stream = util.get_layer_original_style_stream(workspace, layername)
    if style_stream:
        result = {
            'style': {
                'file': style_stream,
            }
        }
    else:
        result = {}
    qgis.delete_layer_dir(workspace, layername)
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
    layer_bbox = info['native_bounding_box']
    crs = info['native_crs']
    table_name = info['db_table']['name']
    layer_bbox = layer_bbox if not bbox_util.is_empty(layer_bbox) else crs_def.CRSDefinitions[crs].default_bbox
    qml = util.get_original_style_xml(workspace, layer)
    qml_geometry = util.get_qml_geometry_from_qml(qml)
    db_types = db.get_geometry_types(workspace, table_name)
    db_cols = [
        col for col in db.get_all_column_infos(workspace, table_name)
        if col.name not in ['wkb_geometry', 'ogc_fid']
    ]
    source_type = util.get_source_type(db_types, qml_geometry)
    layer_qml = util.fill_layer_template(workspace, layer, uuid, layer_bbox, crs, qml, source_type, db_cols, table_name)
    qgs_str = util.fill_project_template(workspace, layer, uuid, layer_qml, crs, settings.LAYMAN_OUTPUT_SRS_LIST,
                                         layer_bbox, source_type, table_name)
    with open(get_layer_file_path(workspace, layer), "w") as qgs_file:
        print(qgs_str, file=qgs_file)


def get_style_qml(workspace, layer):
    style_template_file = util.get_style_template_path()
    layer_template_file = util.get_layer_template_path()
    layer_project_file = get_layer_file_path(workspace, layer)
    original_qml = util.get_original_style_path(workspace, layer)
    return util.get_current_style_xml(style_template_file, layer_template_file, layer_project_file, original_qml)


def wms_direct(wms_url, xml=None, version=None, headers=None):
    version = version or VERSION
    result_wms = WebMapService(wms_url, xml=xml.encode('utf-8') if xml is not None else xml, version=version, headers=headers)
    return result_wms


def get_wms_capabilities(workspace=None, layer=None, headers=None):
    wms_url = get_layer_capabilities_url(workspace, layer)
    return wms_direct(wms_url, headers=headers)
