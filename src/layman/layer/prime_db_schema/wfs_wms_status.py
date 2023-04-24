from layman import patch_mode
from layman.common import empty_method, empty_method_returns_none, empty_method_returns_dict


PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT

get_publication_uuid = empty_method_returns_none
get_layer_info = empty_method_returns_dict
pre_publication_action_check = empty_method
get_metadata_comparison = empty_method_returns_dict
patch_layer = empty_method
post_layer = empty_method
delete_layer = empty_method
