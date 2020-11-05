from layman.common.prime_db_schema import publications as pubs_util
from layman.layer import LAYER_TYPE
from layman import patch_mode

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


def get_layer_infos(username):
    result = {layername: layer_info for (username_value, type, layername), layer_info in pubs_util.get_publication_infos(username, LAYER_TYPE).items()}
    return result


def get_publication_uuid(username, publication_type, publication_name):
    infos = pubs_util.get_publication_infos(username, publication_type)
    return infos.get((username, publication_type, publication_name), dict()).get("uuid")


def get_layer_info(username, layername):
    layers = pubs_util.get_publication_infos(username, LAYER_TYPE)
    info = layers.get((username, LAYER_TYPE, layername), dict())
    return info


def delete_layer(username, layer_name):
    return pubs_util.delete_publication(username, LAYER_TYPE, layer_name)


def patch_layer(username,
                layername,
                title=None,
                can_read=None,
                can_write=None):
    can_read = can_read or set()
    can_write = can_write or set()
    db_info = {"name": layername,
               "title": title,
               "publ_type_name": LAYER_TYPE,
               "can_read": can_read,
               "can_write": can_write,
               }
    pubs_util.update_publication(username, db_info)


def post_layer(username,
               layername,
               title=None,
               uuid=None,
               can_read=None,
               can_write=None):
    can_read = can_read or set()
    can_write = can_write or set()
    db_info = {"name": layername,
               "title": title,
               "publ_type_name": LAYER_TYPE,
               "uuid": uuid,
               "can_read": can_read,
               "can_write": can_write,
               }
    pubs_util.insert_publication(username, db_info)


def get_publication_infos(username, publication_type):
    if publication_type != '.'.join(__name__.split('.')[:-2]):
        raise Exception(f'Unknown pyblication type {publication_type}')

    infos = get_layer_infos(username)
    return infos


def get_metadata_comparison(username, publication_name):
    pass
