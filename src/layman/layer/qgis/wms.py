import os
from owslib.wms import WebMapService

from layman import patch_mode, settings, util as layman_util
from layman.common import bbox as bbox_util, empty_method, empty_method_returns_dict
from layman.util import get_publication_uuid
from . import util, LAYER_TYPE
from .. import db, qgis
from ..layer_class import Layer

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT
VERSION = "1.1.1"

get_metadata_comparison = empty_method_returns_dict
pre_publication_action_check = empty_method
post_layer = empty_method
patch_layer = empty_method


def get_layer_info(workspace, layername, *, x_forwarded_items=None):
    publ_uuid = get_publication_uuid(workspace, LAYER_TYPE, layername)
    return get_layer_info_by_uuid(publ_uuid, x_forwarded_items=x_forwarded_items, layername=layername,
                                  workspace=workspace) if publ_uuid else {}


def get_layer_info_by_uuid(publ_uuid, *, workspace, layername, x_forwarded_items=None):
    input_file_dir = qgis.get_layer_dir(publ_uuid)
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
                'qgis_capabilities_url': get_layer_capabilities_url(publ_uuid),
            }
        }
    return result


def delete_layer(layer: Layer):
    style_stream = util.get_layer_original_style_stream(layer.uuid)
    if style_stream:
        result = {
            'style': {
                'file': style_stream,
            }
        }
    else:
        result = {}
    qgis.delete_layer_dir(layer.uuid)
    return result


def get_layer_capabilities_url(publ_uuid):
    url = f'{settings.LAYMAN_QGIS_URL}?SERVICE=WMS&REQUEST=GetCapabilities&VERSION={VERSION}&map={get_layer_file_path(publ_uuid)}'
    return url


def get_layer_file_path(publ_uuid):
    return os.path.join(qgis.get_layer_dir(publ_uuid), f'{publ_uuid}.qgis')


def save_qgs_file(publ_uuid):
    layer = Layer(uuid=publ_uuid)
    qgis.ensure_layer_dir(layer.uuid)
    table_uri = layer.table_uri
    table_name = table_uri.table
    db_schema = table_uri.schema
    layer_bbox = bbox_util.get_bbox_to_publish(layer.native_bounding_box, layer.native_crs)
    qml = util.get_original_style_xml(publ_uuid)
    db_types = db.get_geometry_types(db_schema, table_name, column_name=table_uri.geo_column, uri_str=table_uri.db_uri_str)
    qml_geometry = util.get_geometry_from_qml_and_db_types(qml, db_types)
    db_cols = [
        col for col in db.get_all_column_infos(db_schema, table_name, uri_str=table_uri.db_uri_str, omit_geometry_columns=True)
        if col.name != table_uri.primary_key_column
    ]
    source_type = util.get_source_type(db_types, qml_geometry)
    column_srid = db.get_column_srid(db_schema, table_name, table_uri.geo_column, uri_str=table_uri.db_uri_str)
    layer_qml = util.fill_layer_template(layer.qgis_names.name, layer.qgis_names.id, layer.title, layer_bbox, layer.native_crs, qml,
                                         source_type, db_cols, table_uri, column_srid, db_types)
    qgs_str = util.fill_project_template(layer.qgis_names.name, layer.qgis_names.id, layer_qml, layer.native_crs,
                                         settings.LAYMAN_OUTPUT_SRS_LIST, layer_bbox, source_type, table_uri, column_srid)
    with open(get_layer_file_path(publ_uuid), "w", encoding="utf-8") as qgs_file:
        print(qgs_str, file=qgs_file)


def get_style_qml(publ_uuid):
    style_template_file = util.get_style_template_path()
    layer_template_file = util.get_layer_template_path()
    layer_project_file = get_layer_file_path(publ_uuid)
    original_qml = util.get_original_style_path(publ_uuid)
    return util.get_current_style_xml(style_template_file, layer_template_file, layer_project_file, original_qml)


def wms_direct(wms_url, xml=None, version=None, headers=None):
    version = version or VERSION
    result_wms = WebMapService(wms_url, xml=xml.encode('utf-8') if xml is not None else xml, version=version, headers=headers)
    return result_wms


def get_wms_capabilities(publ_uuid, headers=None):
    wms_url = get_layer_capabilities_url(publ_uuid)
    return wms_direct(wms_url, headers=headers)
