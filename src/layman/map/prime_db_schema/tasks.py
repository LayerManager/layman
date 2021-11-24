from celery.utils.log import get_task_logger

from layman import celery_app
from layman.celery import AbortedException
from layman.common import bbox as bbox_util, empty_method_returns_true
from .. import util, MAP_TYPE
from ...common.prime_db_schema.publications import set_bbox, set_crs

logger = get_task_logger(__name__)

JSON_EXTENT_CRS = 'EPSG:4326'
refresh_bbox_needed = empty_method_returns_true


@celery_app.task(
    name='layman.map.prime_db_schema.bbox.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_bbox(
        self,
        workspace,
        mapname,
):
    if self.is_aborted():
        raise AbortedException

    mapjson = util.get_map_file_json(workspace, mapname)
    bbox_json = util.get_bbox_from_json(mapjson)
    crs = util.get_crs_from_json(mapjson)
    bbox = bbox_util.transform(bbox_json, JSON_EXTENT_CRS, crs)
    set_bbox(workspace, MAP_TYPE, mapname, bbox, )
    set_crs(workspace, MAP_TYPE, mapname, crs, )

    if self.is_aborted():
        raise AbortedException
