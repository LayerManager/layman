from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman import celery_app
from . import thumbnail

logger = get_task_logger(__name__)


@celery_app.task(
    name='layman.layer.filesystem.thumbnail.patch_after_feature_change',
    bind=True,
    base=celery_app.AbortableTask
)
def patch_after_feature_change(self, workspace, layer):
    if self.is_aborted():
        raise AbortedException
    thumbnail.generate_layer_thumbnail(workspace, layer)

    if self.is_aborted():
        raise AbortedException
