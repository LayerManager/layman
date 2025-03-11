from db import TableUri
from layman.common import empty_method_returns_dict
from layman.common.prime_db_schema import publications as pubs_util
from layman.layer import LAYER_TYPE
from layman import patch_mode, settings
from layman.layer.db import DbNames
from ..layer_class import Layer

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT
get_metadata_comparison = empty_method_returns_dict


def get_layer_info(workspace, layername):
    layers = pubs_util.get_publication_infos(workspace, LAYER_TYPE)
    info = layers.get((workspace, LAYER_TYPE, layername), {})
    if info:
        uuid = info['uuid']
        db_names = DbNames(uuid=uuid)
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
    return pubs_util.delete_publication(layer.workspace, layer.type, layer.name)


def patch_layer(workspace,
                layername,
                actor_name,
                external_table_uri,
                style_type=None,
                title=None,
                description=None,
                access_rights=None,
                image_mosaic=None,
                geodata_type=None,
                ):
    db_info = {"name": layername,
               "title": title,
               "description": description,
               "publ_type_name": LAYER_TYPE,
               "actor_name": actor_name,
               'image_mosaic': image_mosaic,
               'external_table_uri': external_table_uri,
               'geodata_type': geodata_type,
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
               description,
               uuid,
               actor_name,
               geodata_type,
               image_mosaic,
               external_table_uri,
               style_type=None,
               ):
    db_info = {"name": layername,
               "title": title,
               "description": description,
               "publ_type_name": LAYER_TYPE,
               "uuid": uuid,
               "access_rights": access_rights,
               "actor_name": actor_name,
               "geodata_type": geodata_type,
               'style_type': style_type.code if style_type else None,
               'image_mosaic': image_mosaic,
               'external_table_uri': external_table_uri,
               'wfs_wms_status': settings.EnumWfsWmsStatus.PREPARING.value,
               }
    pubs_util.insert_publication(workspace, db_info)


def get_bbox_sphere_size(workspace, layername):
    return pubs_util.get_bbox_sphere_size(workspace, LAYER_TYPE, layername)
