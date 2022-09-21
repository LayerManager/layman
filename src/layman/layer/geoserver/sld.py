import os
from osgeo import gdalconst
from geoserver import util as gs_util
from layman import settings, patch_mode
from layman.common import empty_method, empty_method_returns_none, empty_method_returns_dict
from layman.common.db import launder_attribute_name
from layman.layer.filesystem import input_style
from . import wms
from .. import LAYER_TYPE
from ...util import url_for, get_publication_info

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

get_metadata_comparison = empty_method_returns_dict
pre_publication_action_check = empty_method
post_layer = empty_method
patch_layer = empty_method
get_publication_uuid = empty_method_returns_none


def get_workspace_style_url(workspace, layername):
    layer_info = get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': ['wms']})
    geoserver_workspace = layer_info.get('_wms', {}).get('workspace')
    return gs_util.get_workspace_style_url(geoserver_workspace, layername) if geoserver_workspace else None


def delete_layer(workspace, layername):
    layer_info = get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': ['wms']})
    geoserver_workspace = layer_info.get('_wms', {}).get('workspace')
    sld_stream = gs_util.delete_workspace_style(geoserver_workspace, layername, auth=settings.LAYMAN_GS_AUTH) \
        if geoserver_workspace else None
    wms.clear_cache(workspace)
    if sld_stream:
        result = {
            'style': {
                'file': sld_stream,
            }
        }
    else:
        result = {}
    return result


def get_layer_info(workspace, layername):
    response = get_style_response(workspace, layername, gs_util.headers_sld, settings.LAYMAN_GS_AUTH)
    if response and response.status_code == 200:
        url = url_for('rest_workspace_layer_style.get', workspace=workspace, layername=layername)
        info = {
            'style': {
                'url': url,
                'type': 'sld',
            },
        }
    else:
        info = {}

    return info


def ensure_custom_sld_file_if_needed(workspace, layer):
    # if style already exists, don't use customized SLD style
    if input_style.get_layer_file(workspace, layer):
        return
    info = get_publication_info(workspace, LAYER_TYPE, layer, context={'keys': ['file_type', 'style_type']})
    file_type = info['_file_type']
    style_type = info['_style_type']
    if file_type != settings.FILE_TYPE_RASTER or style_type != 'sld':
        return
    info = get_publication_info(workspace, LAYER_TYPE, layer, {
        'keys': ['file'],
        'extra_keys': [
            '_file.normalized_file.stats',
            '_file.normalized_file.nodata_value',
            '_file.mask_flags',
            '_file.color_interpretations',
        ]})
    file_dict = info['_file']
    input_color_interpretations = file_dict['color_interpretations']
    input_mask_flags = file_dict['mask_flags']
    norm_file_dict = file_dict['normalized_file']
    norm_stats = norm_file_dict['stats']
    norm_nodata_value = norm_file_dict['nodata_value']

    # if there is one grayscale band without mask flags
    if input_color_interpretations == ['Gray'] and input_mask_flags[0].issubset({gdalconst.GMF_ALL_VALID, gdalconst.GMF_NODATA}):
        input_style.ensure_layer_input_style_dir(workspace, layer)
        style_file_path = input_style.get_file_path(workspace, layer, with_extension=False) + '.sld'
        create_customized_grayscale_sld(file_path=style_file_path, min_value=norm_stats[0][0],
                                        max_value=norm_stats[0][1], nodata_value=norm_nodata_value)


def create_customized_grayscale_sld(*, file_path, min_value, max_value, nodata_value):
    nodata_high_entry = ''
    nodata_low_entry = ''
    if nodata_value is not None:
        # if nodata_value > max_value, setting nodata_high_entry seems not necessary
        if nodata_value < min_value:
            nodata_low_entry = f'<sld:ColorMapEntry color="#000000" quantity="{nodata_value}" opacity="0" />'
    with open(os.path.join(DIRECTORY, 'sld_customized_raster_template.sld'), 'r') as template_file:
        template_str = template_file.read()
    xml_str = template_str.format(min_value=min_value, max_value=max_value, nodata_high_entry=nodata_high_entry,
                                  nodata_low_entry=nodata_low_entry)
    with open(file_path, 'w') as file:
        file.write(xml_str)


def create_layer_style(workspace, layername):
    layer_info = get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': ['wms']})
    geoserver_workspace = layer_info['_wms']['workspace']
    style_file = input_style.get_layer_file(workspace, layername)
    gs_util.post_workspace_sld_style(geoserver_workspace, layername, style_file, launder_attribute_name)
    wms.clear_cache(workspace)


def get_style_response(workspace, layername, headers=None, auth=None):
    layer_info = get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': ['wms']})
    geoserver_workspace = layer_info.get('_wms', {}).get('workspace')
    return gs_util.get_workspace_style_response(geoserver_workspace, layername, headers, auth) \
        if geoserver_workspace else None
