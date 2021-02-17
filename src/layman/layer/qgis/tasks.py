from celery.utils.log import get_task_logger

from layman import celery_app
from layman.celery import AbortedException
from . import wms


logger = get_task_logger(__name__)


def refresh_wms_needed(username, layername, task_options):
    return True


@celery_app.task(
    name='layman.layer.qgis.wms.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_wms(
        self,
        username,
        layername,
        store_in_geoserver
):
    if self.is_aborted():
        raise AbortedException

    if not store_in_geoserver:
        wms.save_qgs_file(username, layername)

    if self.is_aborted():
        wms.delete_layer(username, layername)
        raise AbortedException
