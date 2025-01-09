import os
from owslib.wms import WebMapService

import crs as crs_def
from layman import patch_mode, settings, util as layman_util
from layman.common import bbox as bbox_util, empty_method, empty_method_returns_none, empty_method_returns_dict
from . import util, LAYER_TYPE
from .. import db, qgis

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT
VERSION = "1.1.1"

get_metadata_comparison = empty_method_returns_dict
pre_publication_action_check = empty_method
post_layer = empty_method
patch_layer = empty_method
get_publication_uuid = empty_method_returns_none


def get_layer_info(workspace, layername, *, x_forwarded_items=None):
    input_file_dir = qgis.get_layer_dir(workspace, layername)
    result = {}
    if os.path.exists(input_file_dir):
        url = layman_util.url_for('rest_workspace_layer_style.get', workspace=workspace, layername=layername, x_forwarded_items=x_forwarded_items)
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
    info = layman_util.get_publication_info(workspace, LAYER_TYPE, layer, {'keys': ['uuid', 'native_bounding_box',
                                                                                    'table_uri']})
    uuid = info['uuid']
    qgis.ensure_layer_dir(workspace, layer)
    real_bbox = info['native_bounding_box']
    crs = info['native_crs']
    table_uri = info['_table_uri']
    table_name = table_uri.table
    db_schema = table_uri.schema
    layer_bbox = bbox_util.ensure_bbox_with_area(real_bbox, crs_def.CRSDefinitions[crs].no_area_bbox_padding) \
        if not bbox_util.is_empty(real_bbox) else crs_def.CRSDefinitions[crs].default_bbox
    qml = util.get_original_style_xml(workspace, layer)
    db_types = db.get_geometry_types(db_schema, table_name, column_name=table_uri.geo_column, uri_str=table_uri.db_uri_str)
    qml_geometry = util.get_geometry_from_qml_and_db_types(qml, db_types)
    db_cols = [
        col for col in db.get_all_column_infos(db_schema, table_name, uri_str=table_uri.db_uri_str, omit_geometry_columns=True)
        if col.name != table_uri.primary_key_column
    ]
    source_type = util.get_source_type(db_types, qml_geometry)
    column_srid = db.get_column_srid(db_schema, table_name, table_uri.geo_column, uri_str=table_uri.db_uri_str)
    layer_qml = util.fill_layer_template(layer, uuid, layer_bbox, crs, qml, source_type, db_cols, table_uri,
                                         column_srid, db_types)
    qgs_str = util.fill_project_template(layer, uuid, layer_qml, crs, settings.LAYMAN_OUTPUT_SRS_LIST,
                                         layer_bbox, source_type, table_uri, column_srid)
    with open(get_layer_file_path(workspace, layer), "w", encoding="utf-8") as qgs_file:
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
