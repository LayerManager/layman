from functools import partial

from layman.common.filesystem import uuid as common_uuid
from . import input_file

MAP_TYPE = '.'.join(__name__.split('.')[:-2])

# username, mapname
get_map_info = partial(common_uuid.get_publication_info, MAP_TYPE)

# username, mapname
delete_map = partial(common_uuid.delete_publication, MAP_TYPE)

# username, publication_type, publication_name
get_publication_uuid = partial(common_uuid.get_publication_uuid, MAP_TYPE)


def get_map_infos(username):
    infos = input_file.get_map_infos(username)
    for name in infos:
        infos[name]['uuid'] = get_map_uuid(username, name)
    return infos


def get_publication_infos(username, publication_type):
    if publication_type != '.'.join(__name__.split('.')[:-2]):
        raise Exception(f'Unknown pyblication type {publication_type}')

    return get_map_infos(username)


def get_map_uuid(username, mapname):
    return get_publication_uuid(username, MAP_TYPE, mapname)


# username, mapname, uuid_str=None
assign_map_uuid = partial(common_uuid.assign_publication_uuid, MAP_TYPE)


def pre_publication_action_check(username, layername):
    pass


def post_map(username, mapname):
    pass


def patch_map(username, mapname):
    pass


def get_metadata_comparison(username, layername):
    pass
