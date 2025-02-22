import os
from geoserver import util as gs_util
from layman import settings, patch_mode, util as layman_util, names
from layman.common import empty_method, empty_method_returns_dict
from layman.common.db import launder_attribute_name
from layman.layer.layer_class import Layer
from layman.layer.filesystem import input_style
from layman.util import url_for, get_publication_info_by_publication
from . import wms
from .. import LAYER_TYPE

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

get_metadata_comparison = empty_method_returns_dict
pre_publication_action_check = empty_method
post_layer = empty_method
patch_layer = empty_method


def get_workspace_style_url(*, uuid):
    style_name = names.get_layer_names_by_source(uuid=uuid).sld
    return gs_util.get_workspace_style_url(style_name.workspace, style_name.name) if uuid else None


def delete_layer(workspace, layername):
    layer = Layer(layer_tuple=(workspace, layername))
    return delete_layer_by_layer(layer=layer, )


def delete_layer_by_layer(*, layer: Layer):
    gs_style_name = layer.gs_names.sld
    sld_stream = gs_util.delete_workspace_style(gs_style_name.workspace, gs_style_name.name, auth=settings.LAYMAN_GS_AUTH) \
        if layer else None
    wms.clear_cache()
    if sld_stream:
        result = {
            'style': {
                'file': sld_stream,
            }
        }
    else:
        result = {}
    return result


def get_layer_info(workspace, layername, *, x_forwarded_items=None):
    uuid = layman_util.get_publication_uuid(workspace, LAYER_TYPE, layername)
    return get_layer_info_by_uuid(workspace, uuid=uuid, layername=layername, x_forwarded_items=x_forwarded_items)


def get_layer_info_by_uuid(workspace, *, uuid, layername, x_forwarded_items=None):
    response = get_style_response(uuid=uuid, headers=gs_util.headers_sld['1.0.0'], auth=settings.LAYMAN_GS_AUTH)
    if response and response.status_code == 200:
        url = url_for('rest_workspace_layer_style.get', workspace=workspace, layername=layername, x_forwarded_items=x_forwarded_items)
        info = {
            'style': {
                'url': url,
                'type': 'sld',
            },
        }
    else:
        info = {}

    return info


def ensure_custom_sld_file_if_needed(layer: Layer):
    # if style already exists, don't use customized SLD style
    if input_style.get_layer_file(layer.uuid):
        return
    if layer.geodata_type != settings.GEODATA_TYPE_RASTER or layer.style_type != 'sld':
        return
    info = get_publication_info_by_publication(layer, {
        'keys': ['file'],
        'extra_keys': [
            '_file.normalized_file.stats',
            '_file.normalized_file.nodata_value',
            '_file.mask_flags',
            '_file.color_interpretations',
        ]})
    file_dict = info['_file']
    input_color_interpretations = file_dict['color_interpretations']
    norm_file_dict = file_dict['normalized_file']
    norm_stats = norm_file_dict['stats']
    norm_nodata_value = norm_file_dict['nodata_value']

    # if it is grayscale raster (with or without alpha band)
    if input_color_interpretations[0] == 'Gray':
        input_style.ensure_layer_input_style_dir(layer.uuid)
        style_file_path = input_style.get_file_path(layer.uuid, with_extension=False) + '.sld'
        create_customized_grayscale_sld(file_path=style_file_path, min_value=norm_stats[0][0],
                                        max_value=norm_stats[0][1], nodata_value=norm_nodata_value)


def create_customized_grayscale_sld(*, file_path, min_value, max_value, nodata_value):
    nodata_high_entry = ''
    nodata_low_entry = ''
    if nodata_value is not None:
        if nodata_value == 0 and min_value > 0:
            nodata_low_entry = f'<sld:ColorMapEntry color="#000000" quantity="{nodata_value}" opacity="0" label="{nodata_value} no data" />'
    with open(os.path.join(DIRECTORY, 'sld_customized_raster_template.sld'), 'r', encoding="utf-8") as template_file:
        template_str = template_file.read()
    xml_str = template_str.format(min_value=min_value, max_value=max_value, nodata_high_entry=nodata_high_entry,
                                  nodata_low_entry=nodata_low_entry)
    with open(file_path, 'w', encoding="utf-8") as file:
        file.write(xml_str)


def create_layer_style(*, layer: Layer):
    style_file = input_style.get_layer_file(layer.uuid)
    gs_util.post_workspace_sld_style(layer.gs_names.sld.workspace,
                                     layer.gs_names.wms.name,
                                     layer.gs_names.sld.name,
                                     style_file,
                                     launder_attribute_name,
                                     )
    wms.clear_cache()


def get_style_response(*, uuid, headers=None, auth=None):
    gs_style_name = names.get_layer_names_by_source(uuid=uuid).sld
    return gs_util.get_workspace_style_response(gs_style_name.workspace, gs_style_name.name, headers, auth) \
        if uuid else None
