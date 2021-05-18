from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman import celery_app, util as layman_util
from . import soap
from .. import LAYER_TYPE

logger = get_task_logger(__name__)


@celery_app.task(
    name='layman.layer.micka.soap.patch_after_feature_change',
    bind=True,
    base=celery_app.AbortableTask
)
def patch_after_feature_change(
        self,
        workspace,
        layer,
):
    if self.is_aborted():
        raise AbortedException
    uuid = layman_util.get_publication_info(workspace, LAYER_TYPE, layer, context={'keys': ['uuid']})['uuid']

    soap.patch_layer(workspace, layer, metadata_properties_to_refresh=['extent'])

    # Sometimes, when delete request run just after other request for the same publication (for example WFS-T),
    # the aborted task keep running and finish after end of delete task for the same source. This part make sure,
    # that in that case we delete it.
    info = layman_util.get_publication_info(workspace, LAYER_TYPE, layer, context={'keys': ['name']})
    if not info:
        logger.warning(f"layman.layer.micka.soap.patch_after_feature_change: workspace={workspace}, "
                       f"layer={layer}, uuid={uuid} Publication does not exist, so we delete it")
        soap.delete_layer(workspace, layer, backup_uuid=uuid)

    if self.is_aborted():
        raise AbortedException
