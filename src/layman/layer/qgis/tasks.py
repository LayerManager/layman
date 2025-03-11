from celery.utils.log import get_task_logger

from layman import celery_app
from layman.common import empty_method_returns_true
from layman.celery import AbortedException
from . import wms
from ..layer_class import Layer


logger = get_task_logger(__name__)

refresh_wms_needed = empty_method_returns_true


@celery_app.task(
    name='layman.layer.qgis.wms.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
# pylint: disable=unused-argument
def refresh_wms(
        self,
        workspace,
        layername,
        store_in_geoserver,
        uuid,
):
    if self.is_aborted():
        raise AbortedException
    layer = Layer(uuid=uuid)

    if not store_in_geoserver:
        wms.save_qgs_file(layer.uuid)

    if self.is_aborted():
        wms.delete_layer(layer)
        raise AbortedException
