from celery.utils.log import get_task_logger

from layman import celery_app
from layman.celery import AbortedException
from layman.common import bbox as bbox_util
from .. import util, MAP_TYPE
from ...common.prime_db_schema.publications import set_bbox

logger = get_task_logger(__name__)


def refresh_bbox_needed(username, layername, task_options):
    return True


@celery_app.task(
    name='layman.map.prime_db_schema.bbox.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_bbox(
        self,
        username,
        mapname,
):
    if self.is_aborted():
        raise AbortedException

    mapjson = util.get_map_file_json(username, mapname)
    bbox_4326 = util.get_bbox_from_json(mapjson)
    bbox_3857 = bbox_util.transform(bbox_4326, 4326, 3857)
    set_bbox(username, MAP_TYPE, mapname, bbox_3857, )

    if self.is_aborted():
        raise AbortedException
