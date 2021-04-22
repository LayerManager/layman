from functools import partial

from layman import patch_mode
from layman.common.filesystem import uuid as common_uuid

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT

LAYER_TYPE = '.'.join(__name__.split('.')[:-2])

get_layer_info = partial(common_uuid.get_publication_info, LAYER_TYPE)

delete_layer = partial(common_uuid.delete_publication, LAYER_TYPE)

get_publication_uuid = partial(common_uuid.get_publication_uuid, LAYER_TYPE)


def get_layer_uuid(username, layername):
    return get_publication_uuid(username, LAYER_TYPE, layername)


assign_layer_uuid = partial(common_uuid.assign_publication_uuid, LAYER_TYPE)


def pre_publication_action_check(workspace, layername):
    pass


def post_layer(username, layername):
    pass


def patch_layer(workspace, layername):
    pass


def get_metadata_comparison(workspace, publication_name):
    pass
