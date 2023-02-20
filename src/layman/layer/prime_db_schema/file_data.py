from layman import patch_mode, settings
from layman.common import empty_method, empty_method_returns_none, empty_method_returns_dict
from layman.common.prime_db_schema import publications
from .. import LAYER_TYPE

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT

get_publication_uuid = empty_method_returns_none
get_layer_info = empty_method_returns_dict
pre_publication_action_check = empty_method
get_metadata_comparison = empty_method_returns_dict


def delete_layer(workspace, layername):
    publications.set_bbox(workspace, LAYER_TYPE, layername, bbox=(None, None, None, None, ), crs=None)
    layers = publications.get_publication_infos(workspace, LAYER_TYPE)
    info = layers.get((workspace, LAYER_TYPE, layername), dict())
    if info['original_data_source'] == settings.EnumOriginalDataSource.FILE.value:
        publications.set_geodata_type(workspace, LAYER_TYPE, layername, settings.GEODATA_TYPE_UNKNOWN, )


def patch_layer(workspace, layername, *, geodata_type):
    publications.set_geodata_type(workspace, LAYER_TYPE, layername, geodata_type, )


def post_layer(workspace, layername, *, geodata_type):
    publications.set_geodata_type(workspace, LAYER_TYPE, layername, geodata_type, )
