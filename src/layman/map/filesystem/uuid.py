from functools import partial

from layman.common.filesystem import uuid as common_uuid
from . import input_file

MAP_TYPE = '.'.join(__name__.split('.')[:-2])

# username, publication_type
get_publication_names = input_file.get_publication_names

# username
get_map_names = input_file.get_map_names

# username, mapname
get_map_info = partial(common_uuid.get_publication_info, MAP_TYPE)

# username, mapname
delete_map = partial(common_uuid.delete_publication, MAP_TYPE)

# username, publication_type, publication_name
get_publication_uuid = partial(common_uuid.get_publication_uuid, MAP_TYPE)


def get_map_uuid(username, mapname):
    return get_publication_uuid(username, MAP_TYPE, mapname)


# username, mapname, uuid_str=None
assign_map_uuid = partial(common_uuid.assign_publication_uuid, MAP_TYPE)


def post_map(username, mapname):
    pass


def patch_map(username, mapname):
    pass


def get_metadata_comparison(username, layername):
    pass
