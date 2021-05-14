from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman import celery_app
from .. import LAYER_TYPE
from ..db import get_bbox as db_get_bbox
from ...common.prime_db_schema.publications import set_bbox

logger = get_task_logger(__name__)


@celery_app.task(
    name='layman.layer.prime_db_schema.bbox.patch_after_feature_change',
    bind=True,
    base=celery_app.AbortableTask
)
def patch_after_feature_change(
        self,
        username,
        layername,
):
    if self.is_aborted():
        raise AbortedException

    bbox = db_get_bbox(username, layername)

    if self.is_aborted():
        raise AbortedException

    set_bbox(username, LAYER_TYPE, layername, bbox, )

    if self.is_aborted():
        raise AbortedException
