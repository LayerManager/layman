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
             can_read=None,
             can_write=None):
    can_read = can_read or set()
    can_write = can_write or set()
    # store into Layman DB
    db_info = {"name": mapname,
               "title": title,
               "publ_type_name": MAP_TYPE,
               "uuid": uuid,
               "can_read": can_read,
               "can_write": can_write,
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
