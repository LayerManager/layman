from layman.common.prime_db_schema import publications as pubs_util
from layman.layer import LAYER_TYPE
from layman import patch_mode

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


def get_publication_uuid(workspace, publication_type, publication_name):
    infos = pubs_util.get_publication_infos(workspace, publication_type)
    return infos.get((workspace, publication_type, publication_name), dict()).get("uuid")


def get_layer_info(workspace, layername):
    layers = pubs_util.get_publication_infos(workspace, LAYER_TYPE)
    info = layers.get((workspace, LAYER_TYPE, layername), dict())
    return info


def delete_layer(username, layer_name):
    return pubs_util.delete_publication(username, LAYER_TYPE, layer_name)


def patch_layer(username,
                layername,
                actor_name,
                style_type=None,
                title=None,
                access_rights=None,
                ):
    db_info = {"name": layername,
               "title": title,
               "publ_type_name": LAYER_TYPE,
               "actor_name": actor_name,
               }
    if style_type:
        db_info['style_type'] = style_type.code
    if access_rights:
        db_info['access_rights'] = access_rights
    pubs_util.update_publication(username, db_info)


def pre_publication_action_check(workspace,
                                 layername,
                                 actor_name,
                                 access_rights=None,
                                 ):
    db_info = {"name": layername,
               "publ_type_name": LAYER_TYPE,
               "access_rights": access_rights,
               "actor_name": actor_name,
               }
    if access_rights:
        old_info = None
        for type in ['read', 'write']:
            if not access_rights.get(type):
                old_info = old_info or get_layer_info(workspace, layername)
                access_rights[type + '_old'] = old_info['access_rights'][type]
        pubs_util.check_publication_info(workspace, db_info)


def post_layer(username,
               layername,
               access_rights,
               title,
               uuid,
               actor_name,
               style_type=None,
               ):
    db_info = {"name": layername,
               "title": title,
               "publ_type_name": LAYER_TYPE,
               "uuid": uuid,
               "access_rights": access_rights,
               "actor_name": actor_name,
               'style_type': style_type.code if style_type else None,
               }
    pubs_util.insert_publication(username, db_info)


def get_metadata_comparison(workspace, publication_name):
    pass
