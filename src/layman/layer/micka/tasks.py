from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman import celery_app, common
from layman.common import empty_method_returns_true
from layman.common.micka import util as common_util
from . import csw, soap
from ..layer_class import Layer

logger = get_task_logger(__name__)

refresh_soap_needed = empty_method_returns_true


@celery_app.task(
    name='layman.layer.micka.soap.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
# pylint: disable=unused-argument
def refresh_soap(self, username, layername, http_method=common.REQUEST_METHOD_POST,
                 metadata_properties_to_refresh=None, access_rights=None, uuid=None):
    if self.is_aborted():
        raise AbortedException
    layer = Layer(uuid=uuid)
    if http_method == common.REQUEST_METHOD_POST:
        soap.soap_insert(layer, access_rights=access_rights)
    else:
        assert metadata_properties_to_refresh is not None
        common_util.patch_publication_by_soap(layer,
                                              metadata_properties_to_refresh=metadata_properties_to_refresh,
                                              actor_name=None,
                                              access_rights=access_rights,
                                              csw_patch_method=csw.patch_layer_by_class,
                                              soap_insert_method=soap.soap_insert,
                                              )

    if self.is_aborted():
        csw.delete_layer_by_class(layer)
        raise AbortedException
