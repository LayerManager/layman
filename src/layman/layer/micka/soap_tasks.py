from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman import celery_app, util as layman_util
from layman.common.micka import util as micka_util
from . import soap, csw
from ..layer_class import Layer

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
    publication = Layer(layer_tuple=(workspace, layer))

    micka_util.patch_publication_by_soap(publication,
                                         metadata_properties_to_refresh=['extent'],
                                         actor_name=None,
                                         access_rights=None,
                                         csw_patch_method=csw.patch_layer_by_class,
                                         soap_insert_method=soap.soap_insert,
                                         )

    # Sometimes, when delete request run just after other request for the same publication (for example WFS-T),
    # the aborted task keep running and finish after end of delete task for the same source. This part make sure,
    # that in that case we delete it.
    info = layman_util.get_publication_info_by_class(publication, context={'keys': ['name']})
    if not info:
        logger.warning(f"layman.layer.micka.soap.patch_after_feature_change: workspace={publication.workspace}, "
                       f"layer={publication.name}, uuid={publication.uuid} Publication does not exist, so we delete it")
        soap.delete_layer_by_class(publication, backup_uuid=publication.uuid)

    if self.is_aborted():
        raise AbortedException
