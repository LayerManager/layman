from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman import celery_app, common
from layman.common import empty_method_returns_true
from layman.common.micka import util as common_util
from layman.layer import LAYER_TYPE
from . import csw, soap

logger = get_task_logger(__name__)

refresh_csw_needed = empty_method_returns_true
refresh_soap_needed = empty_method_returns_true


@celery_app.task(
    name='layman.layer.micka.csw.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_csw(self, username, layername, http_method=common.REQUEST_METHOD_POST, metadata_properties_to_refresh=None):
    metadata_properties_to_refresh = metadata_properties_to_refresh or []
    if self.is_aborted():
        raise AbortedException
    if http_method == common.REQUEST_METHOD_POST:
        csw.csw_insert(username, layername)
    else:
        csw.patch_layer(username, layername, metadata_properties_to_refresh)

    if self.is_aborted():
        csw.delete_layer(username, layername)
        raise AbortedException


@celery_app.task(
    name='layman.layer.micka.soap.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_soap(self, username, layername, http_method=common.REQUEST_METHOD_POST, metadata_properties_to_refresh=None, access_rights=None):
    if self.is_aborted():
        raise AbortedException
    if http_method == common.REQUEST_METHOD_POST:
        soap.soap_insert(username, layername, access_rights)
    else:
        assert metadata_properties_to_refresh is not None
        common_util.patch_publication_by_soap(workspace=username,
                                              publ_type=LAYER_TYPE,
                                              publ_name=layername,
                                              metadata_properties_to_refresh=metadata_properties_to_refresh,
                                              actor_name=None,
                                              access_rights=access_rights,
                                              csw_patch_method=csw.patch_layer,
                                              soap_insert_method=soap.soap_insert,
                                              )

    if self.is_aborted():
        csw.delete_layer(username, layername)
        raise AbortedException
