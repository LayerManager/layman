from geoserver import util as gs_util
from layman import celery_app, settings, util as layman_util
from layman.celery import AbortedException
from . import wfs
from .. import geoserver, LAYER_TYPE

headers_json = gs_util.headers_json


@celery_app.task(
    name='layman.layer.geoserver.wfs.patch_after_feature_change',
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

    file_type = layman_util.get_publication_info(workspace, LAYER_TYPE, layer, context={'keys': ['file']})['file']['file_type']
    if file_type == settings.FILE_TYPE_RASTER:
        return
    if file_type != settings.FILE_TYPE_VECTOR:
        raise NotImplementedError(f"Unknown file type: {file_type}")

    bbox = geoserver.get_layer_bbox(workspace, layer)
    gs_util.patch_feature_type(workspace, layer, auth=settings.LAYMAN_GS_AUTH, bbox=bbox)
    wfs.clear_cache(workspace)

    if self.is_aborted():
        raise AbortedException
