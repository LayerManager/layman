from layman.common.prime_db_schema import publications as pubs_util
from layman.layer import LAYER_TYPE
from layman import patch_mode

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


def get_layer_infos(username):
    return pubs_util.get_publication_infos(username, LAYER_TYPE)


def get_publication_uuid(username, publication_type, publication_name):
    infos = pubs_util.get_publication_infos(username, publication_type)
    return infos.get(publication_name).get("uuid")


def get_layer_info(username, layername):
    layers = pubs_util.get_publication_infos(username, LAYER_TYPE)
    if layername in layers:
        info = layers[layername]
    else:
        info = {}
    return info


def delete_layer(username, layername):
    pubs_util.delete_publication(username, layername, LAYER_TYPE)


def update_layer(username,
                 layername,
                 layerinfo):
    pass


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


get_publication_infos = pubs_util.get_publication_infos


def get_metadata_comparison(username, publication_name):
    pass
