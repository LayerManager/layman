from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman import celery_app
from ..db import get_bbox as db_get_bbox
from .bbox import set_bbox


logger = get_task_logger(__name__)


def refresh_bbox_needed(username, layername, task_options):
    return True


@celery_app.task(
    name='layman.layer.prime_db_schema.bbox.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_bbox(
        self,
        username,
        layername,
):
    if self.is_aborted():
        raise AbortedException

    bbox = db_get_bbox(username, layername)
    set_bbox(username, layername, bbox, )

    if self.is_aborted():
        raise AbortedException
