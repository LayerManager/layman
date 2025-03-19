from layman import patch_mode, settings
from layman.common import empty_method, empty_method_returns_dict
from layman.common.prime_db_schema import publications
from .. import LAYER_TYPE
from ..layer_class import Layer

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT

get_layer_info = empty_method_returns_dict
pre_publication_action_check = empty_method
get_metadata_comparison = empty_method_returns_dict


def delete_layer(layer: Layer):
    publications.set_bbox(layer.workspace, layer.type, layer.name, bbox=(None, None, None, None, ), crs=None)
    if layer.original_data_source == settings.EnumOriginalDataSource.FILE.value:
        publications.set_geodata_type(layer.workspace, layer.type, layer.name, settings.GEODATA_TYPE_UNKNOWN, )


def patch_layer(layer: Layer):
    publications.set_geodata_type(layer.workspace, layer.type, layer.name, layer.geodata_type)


def post_layer(workspace, layername, *, geodata_type):
    publications.set_geodata_type(workspace, LAYER_TYPE, layername, geodata_type, )
