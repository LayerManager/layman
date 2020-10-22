from functools import partial

from layman import patch_mode
from layman.common.filesystem import uuid as common_uuid
from . import input_file

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT

LAYER_TYPE = '.'.join(__name__.split('.')[:-2])

get_layer_info = partial(common_uuid.get_publication_info, LAYER_TYPE)

delete_layer = partial(common_uuid.delete_publication, LAYER_TYPE)

get_publication_uuid = partial(common_uuid.get_publication_uuid, LAYER_TYPE)


def get_layer_infos(username):
    infos = input_file.get_layer_infos(username)
    for name in infos:
        infos[name]['uuid'] = get_layer_uuid(username, name)
    return infos


def get_publication_infos(username, publication_type):
    if publication_type != '.'.join(__name__.split('.')[:-2]):
        raise Exception(f'Unknown pyblication type {publication_type}')

    return get_layer_infos(username)


def get_layer_uuid(username, layername):
    return get_publication_uuid(username, LAYER_TYPE, layername)


assign_layer_uuid = partial(common_uuid.assign_publication_uuid, LAYER_TYPE)


def post_layer(username, layername):
    pass


patch_layer = partial(common_uuid.update_publication, LAYER_TYPE)


def get_metadata_comparison(username, publication_name):
    pass
