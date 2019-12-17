from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman import celery_app
from . import csw

logger = get_task_logger(__name__)


def refresh_csw_needed(username, layername, task_options):
    return True


@celery_app.task(
    name='layman.layer.micka.csw.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_csw(self, username, layername):
    if self.is_aborted():
        raise AbortedException
    csw.csw_insert(username, layername)

    if self.is_aborted():
        csw.delete_layer(username, layername)
        raise AbortedException

