from ...common.prime_db_schema import publications as pubs_util
from .. import MAP_TYPE


def get_map_infos(username):
    return pubs_util.get_publication_infos(username, MAP_TYPE)


def get_publication_uuid(username, publication_type, publication_name):
    infos = pubs_util.get_publication_infos(username, publication_type)
    return infos.get(publication_name).get("uuid")


def get_map_info(username, mapname):
    maps = pubs_util.get_publication_infos(username, MAP_TYPE)
    if mapname in maps:
        info = maps[mapname]
    else:
        info = {}
    return info


def patch_map(username,
              mapname,
              title=None,
              can_read=None,
              can_write=None):
    can_read = can_read or set()
    can_write = can_write or set()
    db_info = {"name": mapname,
               "title": title,
               "publ_type_name": MAP_TYPE,
               "can_read": can_read,
               "can_write": can_write,
               }
    pubs_util.update_publication(username, db_info)


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


get_publication_infos = pubs_util.get_publication_infos


def delete_map(username, mapname):
    pubs_util.delete_publication(username, mapname, MAP_TYPE)


def get_metadata_comparison(username, publication_name):
    pass
