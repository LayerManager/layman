from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman.common import empty_method_returns_true
from layman import celery_app, common
from . import csw, soap

logger = get_task_logger(__name__)
refresh_soap_needed = empty_method_returns_true


@celery_app.task(
    name='layman.map.micka.soap.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_soap(self, workspace, mapname, http_method=common.REQUEST_METHOD_POST, metadata_properties_to_refresh=None, actor_name=None, access_rights=None):
    if self.is_aborted():
        raise AbortedException
    if http_method == common.REQUEST_METHOD_POST:
        soap.soap_insert(workspace, mapname, access_rights=access_rights, actor_name=actor_name)
    else:
        soap.patch_map(workspace, mapname, metadata_properties_to_refresh=metadata_properties_to_refresh, actor_name=actor_name, access_rights=access_rights)

    if self.is_aborted():
        csw.delete_map(workspace, mapname)
        raise AbortedException
