from layman.db import publications as pubs_util
from .. import MAP_TYPE


def get_map_infos(username):
    return pubs_util.get_publication_infos(username, MAP_TYPE)


def get_map_info(username, mapname):
    maps = pubs_util.get_publication_infos(username, MAP_TYPE)
    if mapname in maps:
        info = maps[mapname]
    else:
        info = {}
    return info


def patch_map(username,
              mapname,
              title=None):
    db_info = {"name": mapname,
               "title": title,
               "publ_type_name": MAP_TYPE,
               "everyone_can_read": True,
               "everyone_can_write": True,
               }
    pubs_util.update_publication(username, db_info)


def post_map(username, mapname, uuid, title):
    # store into Layman DB
    db_info = {"name": mapname,
               "title": title,
               "publ_type_name": MAP_TYPE,
               "uuid": uuid,
               "everyone_can_read": True,
               "everyone_can_write": True,
               }
    pubs_util.insert_publication(username, db_info)


get_publication_infos = pubs_util.get_publication_infos


def delete_map(username, mapname):
    pubs_util.delete_publication(username, mapname, MAP_TYPE)


def get_metadata_comparison(username, publication_name):
    pass
