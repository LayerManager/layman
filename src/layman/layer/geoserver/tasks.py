from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman import celery_app
from layman.layer import geoserver
from . import wms, wfs, sld, ensure_user_workspace

logger = get_task_logger(__name__)

PUBLISH_LAYER_FROM_DB_NAME = 'layman.layer.geoserver.wfs.refresh'


def refresh_wfs_needed(username, layername, task_options):
    return True


@celery_app.task(
    name=PUBLISH_LAYER_FROM_DB_NAME,
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_wfs(
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
        raise AbortedException
    geoserver.publish_layer_from_db(username, layername, description, title)

    if self.is_aborted():
        wms.delete_layer(username, layername)
        wfs.delete_layer(username, layername)
        raise AbortedException


def refresh_sld_needed(username, layername, task_options):
    return True


@celery_app.task(
    name='layman.layer.geoserver.sld.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_sld(self, username, layername):
    if self.is_aborted():
        raise AbortedException
    sld.create_layer_style(username, layername)

    if self.is_aborted():
        sld.delete_layer(username, layername)
        raise AbortedException
