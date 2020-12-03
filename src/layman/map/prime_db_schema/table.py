from ...common.prime_db_schema import publications as pubs_util
from .. import MAP_TYPE


def get_map_infos(username):
    result = {mapname: map_info for (username_value, type, mapname), map_info in pubs_util.get_publication_infos(username, MAP_TYPE).items()}
    return result


def get_publication_uuid(username, publication_type, publication_name):
    infos = pubs_util.get_publication_infos(username, publication_type)
    return infos.get((username, publication_type, publication_name), dict()).get("uuid")


def get_map_info(username, mapname):
    maps = pubs_util.get_publication_infos(username, MAP_TYPE)
    info = maps.get((username, MAP_TYPE, mapname), dict())
    return info


def patch_map(username,
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
    pubs_util.update_publication(username, db_info)


def pre_publication_action_check(username,
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
        pubs_util.check_publication_info(username, db_info)


def post_map(username,
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
               }
    pubs_util.insert_publication(username, db_info)


def get_publication_infos(username, publication_type):
    if publication_type != '.'.join(__name__.split('.')[:-2]):
        raise Exception(f'Unknown pyblication type {publication_type}')

    infos = get_map_infos(username)
    return infos


def delete_map(username, map_name):
    return pubs_util.delete_publication(username, MAP_TYPE, map_name)


def get_metadata_comparison(username, publication_name):
    pass
