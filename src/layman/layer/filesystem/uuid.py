from functools import partial

from layman import patch_mode
from layman.common.filesystem import uuid as common_uuid
from . import input_file

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT

LAYER_TYPE = '.'.join(__name__.split('.')[:-2])

get_publication_names = input_file.get_publication_names

get_layer_infos = input_file.get_layer_infos

get_layer_info = partial(common_uuid.get_publication_info, LAYER_TYPE)

delete_layer = partial(common_uuid.delete_publication, LAYER_TYPE)

get_publication_uuid = partial(common_uuid.get_publication_uuid, LAYER_TYPE)


def get_layer_uuid(username, layername):
    return get_publication_uuid(username, LAYER_TYPE, layername)


assign_layer_uuid = partial(common_uuid.assign_publication_uuid, LAYER_TYPE)

update_layer = partial(common_uuid.update_publication, LAYER_TYPE)


def get_metadata_comparison(username, publication_name):
    pass
