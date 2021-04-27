from functools import partial

from layman import patch_mode
from layman.common import empty_method, empty_method_returns_dict
from layman.common.filesystem import uuid as common_uuid

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT

LAYER_TYPE = '.'.join(__name__.split('.')[:-2])

pre_publication_action_check = empty_method
post_layer = empty_method
patch_layer = empty_method
get_metadata_comparison = empty_method_returns_dict

get_layer_info = partial(common_uuid.get_publication_info, LAYER_TYPE)
delete_layer = partial(common_uuid.delete_publication, LAYER_TYPE)
get_publication_uuid = partial(common_uuid.get_publication_uuid, LAYER_TYPE)
assign_layer_uuid = partial(common_uuid.assign_publication_uuid, LAYER_TYPE)


def get_layer_uuid(username, layername):
    return get_publication_uuid(username, LAYER_TYPE, layername)
