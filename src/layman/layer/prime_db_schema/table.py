from db import TableUri
from layman.common import empty_method_returns_dict
from layman.common.prime_db_schema import publications as pubs_util
from layman.layer import LAYER_TYPE
from layman import patch_mode, settings

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT
get_metadata_comparison = empty_method_returns_dict


def get_publication_uuid(workspace, publication_type, publication_name):
    infos = pubs_util.get_publication_infos(workspace, publication_type)
    return infos.get((workspace, publication_type, publication_name), dict()).get("uuid")


def get_layer_info(workspace, layername):
    layers = pubs_util.get_publication_infos(workspace, LAYER_TYPE)
    info = layers.get((workspace, LAYER_TYPE, layername), dict())
    if info:
        uuid = info['uuid']
        info['_table_uri'] = TableUri(
            db_uri_str=f'postgresql://{settings.LAYMAN_PG_USER}:{settings.LAYMAN_PG_PASSWORD}@{settings.LAYMAN_PG_HOST}:{settings.LAYMAN_PG_PORT}/{settings.LAYMAN_PG_DBNAME}',
            schema=workspace,
            table=f'layer_{uuid.replace("-", "_")}',
            geo_column='wkb_geometry'
        ) if info['_file_type'] == settings.FILE_TYPE_VECTOR and not info.get('_table_uri') else info.get('_table_uri')

    return info


def delete_layer(workspace, layer_name):
    return pubs_util.delete_publication(workspace, LAYER_TYPE, layer_name)


def patch_layer(workspace,
                layername,
                actor_name,
                style_type=None,
                title=None,
                access_rights=None,
                image_mosaic=None,
                ):
    db_info = {"name": layername,
               "title": title,
               "publ_type_name": LAYER_TYPE,
               "actor_name": actor_name,
               'image_mosaic': image_mosaic,
               }
    if style_type:
        db_info['style_type'] = style_type.code
    if access_rights:
        db_info['access_rights'] = access_rights
    pubs_util.update_publication(workspace, db_info)


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


def post_layer(workspace,
               layername,
               access_rights,
               title,
               uuid,
               actor_name,
               file_type,
               image_mosaic,
               external_table_uri,
               style_type=None,
               ):
    db_info = {"name": layername,
               "title": title,
               "publ_type_name": LAYER_TYPE,
               "uuid": uuid,
               "access_rights": access_rights,
               "actor_name": actor_name,
               "file_type": file_type,
               'style_type': style_type.code if style_type else None,
               'image_mosaic': image_mosaic,
               'external_table_uri': external_table_uri,
               }
    pubs_util.insert_publication(workspace, db_info)


def get_bbox_sphere_size(workspace, layername):
    return pubs_util.get_bbox_sphere_size(workspace, LAYER_TYPE, layername)
