from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman import celery_app
from . import thumbnail

logger = get_task_logger(__name__)


def refresh_thumbnail_needed(username, layername, task_options):
    return True


@celery_app.task(
    name='layman.map.filesystem.thumbnail.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_thumbnail(self, username, mapname):
    if self.is_aborted():
        raise AbortedException
    thumbnail.generate_map_thumbnail(username, mapname)

    if self.is_aborted():
        thumbnail.delete_map(username, mapname)
        raise AbortedException

