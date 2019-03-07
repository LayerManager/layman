from celery.utils.log import get_task_logger

from layman import celery_app
from layman.layer import geoserver
from . import wms, wfs, sld, ensure_user_workspace

logger = get_task_logger(__name__)

@celery_app.task(
    name='layman.layer.geoserver.publish_layer_from_db',
    bind=True,
    base=celery_app.AbortableTask
)
def publish_layer_from_db(
        self,
        username,
        layername,
        description=None,
        title=None,
        ensure_user=False
    ):
    if description is None:
        description = layername
    if title is None:
        title = layername
    if ensure_user:
        ensure_user_workspace(username)

    if self.is_aborted():
        return
    geoserver.publish_layer_from_db(username, layername, description, title)

    if self.is_aborted():
        wms.delete_layer(username, layername)
        wfs.delete_layer(username, layername)

@celery_app.task(
    name='layman.layer.geoserver.sld.create_layer_style',
    bind=True,
    base=celery_app.AbortableTask
)
def create_layer_style(self, username, layername):
    if self.is_aborted():
        return
    sld.create_layer_style(username, layername)

    if self.is_aborted():
        sld.delete_layer(username, layername)

