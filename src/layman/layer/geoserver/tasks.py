from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman import celery_app
from . import wms, wfs, sld
from .. import geoserver

logger = get_task_logger(__name__)


def refresh_wms_needed(username, layername, task_options):
    return True


@celery_app.task(
    name='layman.layer.geoserver.wms.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_wms(
        self,
        username,
        layername,
        description=None,
        title=None,
        ensure_user=False,
        access_rights=None,
):
    if description is None:
        description = layername
    if title is None:
        title = layername
    geoserver_workspace = wms.get_geoserver_workspace(username)
    if ensure_user:
        geoserver.ensure_workspace(username)

    if self.is_aborted():
        raise AbortedException
    geoserver.publish_layer_from_db(username, layername, description, title, access_rights, geoserver_workspace=geoserver_workspace)
    wms.clear_cache(username)

    if self.is_aborted():
        wms.delete_layer(username, layername)
        raise AbortedException


def refresh_wfs_needed(username, layername, task_options):
    return True


@celery_app.task(
    name='layman.layer.geoserver.wfs.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_wfs(
        self,
        username,
        layername,
        description=None,
        title=None,
        ensure_user=False,
        access_rights=None,
):
    if description is None:
        description = layername
    if title is None:
        title = layername
    if ensure_user:
        geoserver.ensure_workspace(username)

    if self.is_aborted():
        raise AbortedException
    geoserver.publish_layer_from_db(username, layername, description, title, access_rights)
    wfs.clear_cache(username)

    if self.is_aborted():
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
