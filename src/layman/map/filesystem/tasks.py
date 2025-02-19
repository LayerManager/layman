from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman.common import empty_method_returns_true
from layman import celery_app
from . import thumbnail

logger = get_task_logger(__name__)
refresh_thumbnail_needed = empty_method_returns_true


@celery_app.task(
    name='layman.map.filesystem.thumbnail.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
# pylint: disable=unused-argument
def refresh_thumbnail(self, workspace, mapname, uuid, actor_name=None):
    if self.is_aborted():
        raise AbortedException
    thumbnail.generate_map_thumbnail(uuid, editor=actor_name)

    if self.is_aborted():
        thumbnail.delete_map_by_uuid(uuid)
        raise AbortedException
