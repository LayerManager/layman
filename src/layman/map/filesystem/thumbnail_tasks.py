from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman import celery_app, util as layman_util
from . import thumbnail

logger = get_task_logger(__name__)


@celery_app.task(
    name='layman.map.filesystem.thumbnail.patch_after_feature_change',
    bind=True,
    base=celery_app.AbortableTask
)
# pylint: disable=unused-argument
def patch_after_feature_change(self, uuid):
    if self.is_aborted():
        raise AbortedException

    editor = layman_util.get_publication_writer(uuid)
    thumbnail.generate_map_thumbnail(uuid, editor=editor)

    if self.is_aborted():
        raise AbortedException
