from layman import patch_mode
from layman.common import empty_method, empty_method_returns_dict, empty_method_returns_none

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT

LAYER_TYPE = '.'.join(__name__.split('.')[:-2])

pre_publication_action_check = empty_method
post_layer = empty_method
patch_layer = empty_method
get_metadata_comparison = empty_method_returns_dict

get_layer_info = empty_method_returns_dict
delete_layer = empty_method
get_publication_uuid = empty_method_returns_none
