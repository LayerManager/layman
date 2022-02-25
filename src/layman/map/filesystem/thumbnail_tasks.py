from celery.utils.log import get_task_logger

import layman_settings
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

    info = layman_util.get_publication_info(workspace, MAP_TYPE, map, context={'keys': ['access_rights']})
    write_rights = info.get('access_rights', {}).get('write', [])
    writers = [write_right for write_right in write_rights if write_right != layman_settings.RIGHTS_EVERYONE_ROLE]
    editor = next(iter(writers), layman_settings.ANONYM_USER)

    thumbnail.generate_map_thumbnail(workspace, map, editor=editor)

    if self.is_aborted():
        raise AbortedException
