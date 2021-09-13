from functools import partial

from layman.common import empty_method, empty_method_returns_dict
from layman.common.filesystem import uuid as common_uuid

MAP_TYPE = '.'.join(__name__.split('.')[:-2])

# workspace, mapname
get_map_info = partial(common_uuid.get_publication_info, MAP_TYPE)

# workspace, mapname
delete_map = partial(common_uuid.delete_publication, MAP_TYPE)

# workspace, publication_type, publication_name
get_publication_uuid = partial(common_uuid.get_publication_uuid, MAP_TYPE)


def get_map_uuid(workspace, mapname):
    return get_publication_uuid(workspace, MAP_TYPE, mapname)


# workspace, mapname, uuid_str=None
assign_map_uuid = partial(common_uuid.assign_publication_uuid, MAP_TYPE)


pre_publication_action_check = empty_method
post_map = empty_method
patch_map = empty_method
get_metadata_comparison = empty_method_returns_dict
