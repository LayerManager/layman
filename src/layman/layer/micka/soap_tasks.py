from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman import celery_app
from . import soap

logger = get_task_logger(__name__)


@celery_app.task(
    name='layman.layer.micka.soap.patch_after_wfst',
    bind=True,
    base=celery_app.AbortableTask
)
def patch_after_wfst(
        self,
        workspace,
        layer,
):
    if self.is_aborted():
        raise AbortedException

    soap.patch_layer(workspace, layer, metadata_properties_to_refresh=['extent'])

    if self.is_aborted():
        raise AbortedException
