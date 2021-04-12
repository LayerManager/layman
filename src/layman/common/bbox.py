from layman.common.prime_db_schema import util as db_util


def is_empty(bbox):
    return all(num is None for num in bbox)


def transform(bbox, epsg_from=4326, epsg_to=3857):
    query = f'''
    with tmp as (select ST_Transform(ST_SetSRID(ST_MakeBox2D(ST_Point(%s, %s), ST_Point(%s, %s)), %s), %s) bbox)
    select st_xmin(bbox),
           st_ymin(bbox),
           st_xmax(bbox),
           st_ymax(bbox)
    from tmp
    ;'''
    params = bbox + (epsg_from, epsg_to,)
    result = db_util.run_query(query, params)[0]
    return result
