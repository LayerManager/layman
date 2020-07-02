from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman import celery_app
from . import csw, soap

logger = get_task_logger(__name__)


def refresh_csw_needed(username, mapname, task_options):
    return True


@celery_app.task(
    name='layman.map.micka.csw.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_csw(self, username, mapname, http_method='post', metadata_properties_to_refresh=None):
    if self.is_aborted():
        raise AbortedException
    if http_method == 'post':
        csw.csw_insert(username, mapname)
    else:
        csw.patch_map(username, mapname, metadata_properties_to_refresh=metadata_properties_to_refresh)

    if self.is_aborted():
        csw.delete_map(username, mapname)
        raise AbortedException


def refresh_soap_needed(username, mapname, task_options):
    return True


@celery_app.task(
    name='layman.map.micka.soap.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_soap(self, username, mapname, http_method='post', metadata_properties_to_refresh=None):
    if self.is_aborted():
        raise AbortedException
    if http_method == 'post':
        soap.soap_insert(username, mapname)
    else:
        csw.patch_map(username, mapname, metadata_properties_to_refresh=metadata_properties_to_refresh)

    if self.is_aborted():
        csw.delete_map(username, mapname)
        raise AbortedException
