from celery.utils.log import get_task_logger

from layman import celery_app
from layman.celery import AbortedException
from . import thumbnail

logger = get_task_logger(__name__)


@celery_app.task(
    name='layman.layer.filesystem.thumbnail.patch_after_feature_change',
    bind=True,
    base=celery_app.AbortableTask
)
def patch_after_feature_change(self, uuid):
    if self.is_aborted():
        raise AbortedException
    thumbnail.generate_layer_thumbnail(uuid)

    if self.is_aborted():
        raise AbortedException
