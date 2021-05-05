from geoserver import util as gs_util
from layman import celery_app, settings
from layman.celery import AbortedException
from . import wfs
from .. import geoserver

headers_json = geoserver.headers_json


@celery_app.task(
    name='layman.layer.geoserver.wfs.patch_after_wfst',
    bind=True,
    base=celery_app.AbortableTask
)
def patch_after_wfst(
        self,
        workspace,
        layer,
):
    if self.is_aborted():
        raise AbortedException

    bbox = geoserver.get_layer_bbox(workspace, layer)
    gs_util.patch_feature_type(workspace, layer, auth=settings.LAYMAN_GS_AUTH, bbox=bbox)
    wfs.clear_cache(workspace)

    if self.is_aborted():
        raise AbortedException
