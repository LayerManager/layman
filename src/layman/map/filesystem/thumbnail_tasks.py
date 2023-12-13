from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman import celery_app, util as layman_util
from . import thumbnail
from .. import MAP_TYPE

logger = get_task_logger(__name__)


@celery_app.task(
    name='layman.map.filesystem.thumbnail.patch_after_feature_change',
    bind=True,
    base=celery_app.AbortableTask
)
def patch_after_feature_change(self, workspace, map):
    if self.is_aborted():
        raise AbortedException

    editor = layman_util.get_publication_writer(workspace, MAP_TYPE, map)

    thumbnail.generate_map_thumbnail(workspace, map, editor=editor)

    if self.is_aborted():
        raise AbortedException
