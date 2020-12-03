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
                actor_name,
                title=None,
                access_rights=None):
    db_info = {"name": layername,
               "title": title,
               "publ_type_name": LAYER_TYPE,
               "actor_name": actor_name,
               }
    if access_rights:
        db_info['access_rights'] = access_rights
    pubs_util.update_publication(username, db_info)


def pre_post_publication_check(username, layername, access_rights, actor_name,):
    db_info = {"name": layername,
               "publ_type_name": LAYER_TYPE,
               "access_rights": access_rights,
               "actor_name": actor_name,
               }
    pubs_util.check_publication_info(username, db_info)


def post_layer(username,
               layername,
               access_rights,
               title,
               uuid,
               actor_name,
               ):
    db_info = {"name": layername,
               "title": title,
               "publ_type_name": LAYER_TYPE,
               "uuid": uuid,
               "access_rights": access_rights,
               "actor_name": actor_name,
               }
    pubs_util.insert_publication(username, db_info)


def get_publication_infos(username, publication_type):
    if publication_type != '.'.join(__name__.split('.')[:-2]):
        raise Exception(f'Unknown pyblication type {publication_type}')

    infos = get_layer_infos(username)
    return infos


def get_metadata_comparison(username, publication_name):
    pass
