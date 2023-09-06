from layman.common import empty_method_returns_dict
from . import util
from ...common.prime_db_schema import publications as pubs_util
from .. import MAP_TYPE

get_metadata_comparison = empty_method_returns_dict


def get_publication_uuid(workspace, publication_type, publication_name):
    infos = pubs_util.get_publication_infos(workspace, publication_type)
    return infos.get((workspace, publication_type, publication_name), {}).get("uuid")


def get_map_info(workspace, mapname):
    maps = pubs_util.get_publication_infos(workspace, MAP_TYPE)
    info = maps.get((workspace, MAP_TYPE, mapname), {})
    if info:
        info.pop('_table_uri', None)
        info.pop('_wfs_wms_status', None)
        info.pop('original_data_source', None)
        info.pop('geodata_type', None)
    return info


def patch_map(workspace,
              mapname,
              actor_name,
              title=None,
              access_rights=None):
    db_info = {"name": mapname,
               "title": title,
               "publ_type_name": MAP_TYPE,
               "actor_name": actor_name,
               }
    if access_rights:
        db_info['access_rights'] = access_rights
    pubs_util.update_publication(workspace, db_info)


def pre_publication_action_check(workspace,
                                 layername,
                                 actor_name,
                                 access_rights=None,
                                 ):
    db_info = {"name": layername,
               "publ_type_name": MAP_TYPE,
               "access_rights": access_rights,
               "actor_name": actor_name,
               }
    if access_rights:
        old_info = None
        for type in ['read', 'write']:
            if not access_rights.get(type):
                old_info = old_info or get_map_info(workspace, layername)
                access_rights[type + '_old'] = old_info['access_rights'][type]
        pubs_util.check_publication_info(workspace, db_info)


def post_map(workspace,
             mapname,
             uuid,
             title,
             access_rights,
             actor_name,
             ):
    # store into Layman DB
    db_info = {"name": mapname,
               "title": title,
               "publ_type_name": MAP_TYPE,
               "uuid": uuid,
               "access_rights": access_rights,
               "actor_name": actor_name,
               'image_mosaic': False,
               }
    pubs_util.insert_publication(workspace, db_info)


def delete_map(workspace, map_name):
    util.delete_internal_layer_relations(workspace, map_name, )
    return pubs_util.delete_publication(workspace, MAP_TYPE, map_name)
