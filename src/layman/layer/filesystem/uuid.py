import os

from layman.uuid import register_publication_uuid, delete_publication_uuid
from . import input_file
from . import util


LAYER_SUBFILE = 'uuid.txt'


get_publication_names = input_file.get_publication_names


get_layer_names = input_file.get_layer_names


def get_layer_info(username, layername):
    uuid_str = get_layer_uuid(username, layername)
    if uuid_str is not None:
        return {
            'uuid': uuid_str,
        }
    else:
        return {}


def delete_layer(username, layername):
    uuid_str = get_layer_uuid(username, layername)
    if uuid_str is not None:
        delete_publication_uuid(uuid_str)
    util.delete_layer_subfile(username, layername, LAYER_SUBFILE)


def get_publication_uuid(username, publication_type, publication_name):
    if publication_type != '.'.join(__name__.split('.')[:-2]):
        raise Exception(f'Unknown publication type {publication_type}')
    return get_layer_uuid(username, publication_name)


def get_layer_uuid_file(username, layername):
    uuid_file = os.path.join(util.get_layer_dir(username, layername),
                                 LAYER_SUBFILE)
    return uuid_file


def get_layer_uuid(username, layername):
    uuid_path = get_layer_uuid_file(username, layername)
    if not os.path.exists(uuid_path):
        return None
    else:
        with open(uuid_path, "r") as uuid_file:
            uuid_str = uuid_file.read().strip()
            return uuid_str


def assign_layer_uuid(username, layername, uuid_str=None):
    uuid_str = register_publication_uuid(username, '.'.join(__name__.split('.')[:-2]), layername, uuid_str)
    uuid_path = get_layer_uuid_file(username, layername)
    util.ensure_layer_dir(username, layername)
    with open(uuid_path, "w") as uuid_file:
        uuid_file.write(uuid_str)
    return uuid_str


def update_layer(username, layername, layerinfo):
    if 'uuid' in layerinfo:
        new_uuid = layerinfo['uuid']
        old_uuid = get_layer_uuid(username, layername)
        if old_uuid is not None:
            if old_uuid != new_uuid:
                raise Exception(f'Layer {username}/{layername} already has UUID {old_uuid} that differs from updated UUID {new_uuid}')
        elif new_uuid is not None:
            assign_layer_uuid(username, layername, new_uuid)


