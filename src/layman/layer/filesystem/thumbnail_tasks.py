from celery.utils.log import get_task_logger

from layman import celery_app
from layman.celery import AbortedException
from layman.layer import LAYER_TYPE
from layman.util import get_publication_uuid
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
    publ_uuid = get_publication_uuid(workspace, LAYER_TYPE, layer)
    thumbnail.generate_layer_thumbnail(publ_uuid)

    if self.is_aborted():
        raise AbortedException
