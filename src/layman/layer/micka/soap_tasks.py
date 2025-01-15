from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman import celery_app, util as layman_util
from layman.common.micka import util as micka_util
from . import soap, csw
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

    micka_util.patch_publication_by_soap(workspace=workspace,
                                         publ_type=LAYER_TYPE,
                                         publ_name=layer,
                                         metadata_properties_to_refresh=['extent'],
                                         actor_name=None,
                                         access_rights=None,
                                         csw_patch_method=csw.patch_layer,
                                         soap_insert_method=soap.soap_insert,
                                         )

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
