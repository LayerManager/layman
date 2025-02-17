from layman.common import empty_method, empty_method_returns_dict, empty_method_returns_none

MAP_TYPE = '.'.join(__name__.split('.')[:-2])

# workspace, mapname
get_map_info = empty_method_returns_dict

# workspace, mapname
delete_map = empty_method

# workspace, publication_type, publication_name
get_publication_uuid = empty_method_returns_none


pre_publication_action_check = empty_method
post_map = empty_method
patch_map = empty_method
get_metadata_comparison = empty_method_returns_dict
