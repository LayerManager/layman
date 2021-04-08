from collections import defaultdict
from layman.common.prime_db_schema import util as db_util
from layman.util import USERNAME_PATTERN, USERNAME_ONLY_PATTERN


PUBLICATION_NAME_ONLY_PATTERN = USERNAME_ONLY_PATTERN
PUBLICATION_NAME_PATTERN = USERNAME_PATTERN


def merge_infos(infos):
    result_infos = defaultdict(dict)
    for source in infos:
        for (name, info) in source.items():
            result_infos[name].update(info)
    return result_infos


def clear_publication_info(info):
    for key in ['id', 'type', 'style_type']:
        try:
            del info[key]
        except KeyError:
            pass
    info['updated_at'] = info['updated_at'].isoformat()
    return info


def bbox_is_empty(bbox):
    return all(num is None for num in bbox)


def convert_bbox(bbox, epsg_from=4326, epsg_to=3857):
    query = f'''
    with tmp as (select ST_Transform(ST_SetSRID(ST_MakeBox2D(ST_Point(%s, %s), ST_Point(%s, %s)), %s), %s) bbox)
    select st_xmin(bbox),
           st_ymin(bbox),
           st_xmax(bbox),
           st_ymax(bbox)
    from tmp
    ;'''
    params = bbox + (epsg_from, epsg_to, )
    result = db_util.run_query(query, params)[0]
    return result
