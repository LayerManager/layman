from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman import celery_app, util as layman_util
from layman.util import get_publication_uuid
from . import thumbnail
from .. import MAP_TYPE

logger = get_task_logger(__name__)


@celery_app.task(
    name='layman.map.filesystem.thumbnail.patch_after_feature_change',
    bind=True,
    base=celery_app.AbortableTask
)
# pylint: disable=unused-argument
def patch_after_feature_change(self, workspace, map):
    if self.is_aborted():
        raise AbortedException

    editor = layman_util.get_publication_writer(workspace, MAP_TYPE, map)

    publ_uuid = get_publication_uuid(workspace, MAP_TYPE, map)
    thumbnail.generate_map_thumbnail(publ_uuid, editor=editor)

    if self.is_aborted():
        raise AbortedException
