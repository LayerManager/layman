from celery.utils.log import get_task_logger

from layman import celery_app, util as layman_util
from layman.celery import AbortedException
from . import wms
from .. import LAYER_TYPE

logger = get_task_logger(__name__)


@celery_app.task(
    name='layman.layer.qgis.wms.patch_after_feature_change',
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

    style_type = layman_util.get_publication_info(workspace, LAYER_TYPE, layer, context={'keys': ['style_type'], })['_style_type']
    if style_type == 'qml':
        wms.save_qgs_file(workspace, layer)

    if self.is_aborted():
        raise AbortedException
