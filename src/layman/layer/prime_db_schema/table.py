from db import TableUri
from layman.common import empty_method_returns_dict
from layman.common.prime_db_schema import publications as pubs_util
from layman.layer import LAYER_TYPE
from layman import patch_mode, settings
from layman.layer.db import DbIds
from ..layer_class import Layer

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT
get_metadata_comparison = empty_method_returns_dict


def get_layer_info(uuid):
    info = pubs_util.get_publication_info(uuid, pub_type=LAYER_TYPE) or {}
    if info:
        uuid = info['uuid']
        db_names = DbIds(uuid=uuid)
        info['_table_uri'] = TableUri(
            db_uri_str=settings.PG_URI_STR,
            schema=db_names.schema,
            table=db_names.table,
            geo_column=settings.OGR_DEFAULT_GEOMETRY_COLUMN,
            primary_key_column=settings.OGR_DEFAULT_PRIMARY_KEY,
        ) if info['geodata_type'] == settings.GEODATA_TYPE_VECTOR and not info.get('_table_uri') else info.get('_table_uri')

        info.pop('_map_layers', None)

    return info


def delete_layer(layer: Layer):
    return pubs_util.delete_publication(layer.uuid)


def patch_layer(layer: Layer,
                actor_name,
                external_table_uri,
                is_part_of_user_delete=False,
                access_rights=None,
                ):
    db_info = {"name": layer.name,
               "title": layer.title,
               "description": layer.description,
               "publ_type_name": layer.type,
               "actor_name": actor_name,
               'image_mosaic': layer.image_mosaic,
               'external_table_uri': external_table_uri,
               'geodata_type': layer.geodata_type,
               }
    if layer.style_type:
        db_info['style_type'] = layer.style_type
    if access_rights:
        db_info['access_rights'] = access_rights
    pubs_util.update_publication(layer.uuid, db_info, is_part_of_user_delete)


def pre_publication_action_check(layer: Layer,
                                 actor_name,
                                 access_rights=None,
                                 ):
    db_info = {"name": layer.name,
               "publ_type_name": layer.type,
               "access_rights": access_rights,
               "actor_name": actor_name,
               }
    if access_rights:
        old_info = None
        for type in ['read', 'write']:
            if not access_rights.get(type):
                old_info = old_info or get_layer_info(layer.uuid)
                access_rights[type + '_old'] = old_info['access_rights'][type]
        pubs_util.check_publication_info(layer.workspace, db_info)


def post_layer(layer: Layer,
               access_rights,
               title,
               description,
               actor_name,
               geodata_type,
               image_mosaic,
               external_table_uri,
               style_type=None,
               ):
    db_info = {"name": layer.name,
               "title": title,
               "description": description,
               "publ_type_name": layer.type,
               "uuid": layer.uuid,
               "access_rights": access_rights,
               "actor_name": actor_name,
               "geodata_type": geodata_type,
               'style_type': style_type.code if style_type else None,
               'image_mosaic': image_mosaic,
               'external_table_uri': external_table_uri,
               'wfs_wms_status': settings.EnumWfsWmsStatus.PREPARING.value,
               }
    pubs_util.insert_publication(layer.workspace, db_info)


def get_bbox_sphere_size(layer: Layer):
    return pubs_util.get_bbox_sphere_size(layer.uuid)
