import logging
import crs as crs_def
from db import util as db_util

logger = logging.getLogger(__name__)


def is_empty(bbox):
    return all(num is None for num in bbox)


def is_valid(coords):
    return len(coords) == 4 \
        and coords.count(None) in {0, 4} \
        and (is_empty(coords) or (coords[0] <= coords[2] and coords[1] <= coords[3]))


def contains_bbox(bbox1, bbox2, *, precision=0):
    return not is_empty(bbox1) and not is_empty(bbox2) \
        and all(bbox1[i] <= bbox2[i] + precision for i in [0, 1]) \
        and all(bbox2[i] <= bbox1[i] + precision for i in [2, 3])


def intersects(bbox1, bbox2):
    return not is_empty(bbox1) and not is_empty(bbox2) \
        and bbox1[0] <= bbox2[2] and bbox1[2] >= bbox2[0] and bbox1[1] <= bbox2[3] and bbox1[3] >= bbox2[1]


def get_intersection(bbox1, bbox2):
    intersection = [None] * 4
    if intersects(bbox1, bbox2):
        if bbox1[0] > bbox2[0]:
            intersection[0] = bbox1[0]
        else:
            intersection[0] = bbox2[0]
        if bbox1[1] > bbox2[1]:
            intersection[1] = bbox1[1]
        else:
            intersection[1] = bbox2[1]
        if bbox1[2] < bbox2[2]:
            intersection[2] = bbox1[2]
        else:
            intersection[2] = bbox2[2]
        if bbox1[3] < bbox2[3]:
            intersection[3] = bbox1[3]
        else:
            intersection[3] = bbox2[3]
    return intersection


def has_area(bbox):
    return not is_empty(bbox) and bbox[0] != bbox[2] and bbox[1] != bbox[3]


def get_area(bbox):
    return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])


def ensure_bbox_with_area(bbox, no_area_padding):
    result = bbox
    if not has_area(bbox):
        result = list(result)
        if result[0] == result[2]:
            result[0] -= no_area_padding
            result[2] += no_area_padding
        if result[1] == result[3]:
            result[1] -= no_area_padding
            result[3] += no_area_padding
        result = tuple(result)
    return result


def get_bbox_to_publish(native_bbox, native_crs):
    result = ensure_bbox_with_area(native_bbox, crs_def.CRSDefinitions[native_crs].no_area_bbox_padding) \
        if not is_empty(native_bbox) else crs_def.CRSDefinitions[native_crs].default_bbox
    return result


def transform(bbox, crs_from, crs_to):
    if is_empty(bbox):
        return None, None, None, None
    srid_from = db_util.get_internal_srid(crs_from)
    srid_to = db_util.get_internal_srid(crs_to)
    world_bounds = crs_def.CRSDefinitions[crs_to].world_bounds.get(crs_from)
    if world_bounds:
        bbox = (
            min(max(bbox[0], world_bounds[0]), world_bounds[2]),
            min(max(bbox[1], world_bounds[1]), world_bounds[3]),
            max(min(bbox[2], world_bounds[2]), world_bounds[0]),
            max(min(bbox[3], world_bounds[3]), world_bounds[1]),
        )

    query = f'''
    with tmp as (select ST_Transform(ST_SetSRID(ST_MakeBox2D(ST_Point(%s, %s),
                                                             ST_Point(%s, %s)),
                                                %s),
                                     %s) bbox)
    select st_xmin(bbox),
           st_ymin(bbox),
           st_xmax(bbox),
           st_ymax(bbox)
    from tmp
    ;'''
    params = tuple(bbox) + (srid_from, srid_to,)
    result = db_util.run_query(query, params)[0]
    max_bbox = crs_def.CRSDefinitions[crs_to].max_bbox
    result = (
        min(max(result[0], max_bbox[0]), max_bbox[2]),
        min(max(result[1], max_bbox[1]), max_bbox[3]),
        max(min(result[2], max_bbox[2]), max_bbox[0]),
        max(min(result[3], max_bbox[3]), max_bbox[1]),
    ) if max_bbox else result
    return result


def are_similar(bbox1, bbox2, *, no_area_bbox_padding=None, limit=0.95):
    if not has_area(bbox1):
        assert no_area_bbox_padding is not None and no_area_bbox_padding > 0
        bbox1 = ensure_bbox_with_area(bbox1, no_area_bbox_padding)
    if not has_area(bbox2):
        assert no_area_bbox_padding is not None and no_area_bbox_padding > 0
        bbox2 = ensure_bbox_with_area(bbox2, no_area_bbox_padding)
    isect = get_intersection(bbox1, bbox2)
    if is_empty(isect):
        return False

    a_area = get_area(bbox1)
    b_area = get_area(bbox2)
    i_area = get_area(isect)

    similarity = i_area / a_area * i_area / b_area
    # current_app.logger.info(f"a={a}, b={b}, similarity={similarity}")
    return similarity >= limit
