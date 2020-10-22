from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman import celery_app
from . import csw, soap

logger = get_task_logger(__name__)


def refresh_csw_needed(username, layername, task_options):
    return True


@celery_app.task(
    name='layman.layer.micka.csw.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_csw(self, username, layername, http_method='post', metadata_properties_to_refresh=None):
    metadata_properties_to_refresh = metadata_properties_to_refresh or []
    if self.is_aborted():
        raise AbortedException
    if http_method == 'post':
        csw.csw_insert(username, layername)
    else:
        csw.update_layer(username, layername, metadata_properties_to_refresh)

    if self.is_aborted():
        csw.delete_layer(username, layername)
        raise AbortedException


def refresh_soap_needed(username, layername, task_options):
    return True


@celery_app.task(
    name='layman.layer.micka.soap.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_soap(self, username, layername, http_method='post', metadata_properties_to_refresh=None):
    metadata_properties_to_refresh = metadata_properties_to_refresh or []
    if self.is_aborted():
        raise AbortedException
    if http_method == 'post':
        soap.soap_insert(username, layername)
    else:
        csw.update_layer(username, layername, metadata_properties_to_refresh)

    if self.is_aborted():
        csw.delete_layer(username, layername)
        raise AbortedException
