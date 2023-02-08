from geoserver import util as gs_util
from layman import celery_app, settings, util as layman_util
from layman.celery import AbortedException
from . import wfs, get_external_db_store_name
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

    info = layman_util.get_publication_info(workspace, LAYER_TYPE, layer,
                                            context={'keys': ['file_type', 'native_crs', 'is_external_table']})
    file_type = info['_file_type']
    if file_type == settings.FILE_TYPE_RASTER:
        return
    if file_type != settings.FILE_TYPE_VECTOR:
        raise NotImplementedError(f"Unknown file type: {file_type}")

    bbox = geoserver.get_layer_bbox(workspace, layer)
    crs = info['native_crs']
    is_external_table = info['_is_external_table']
    store_name = get_external_db_store_name(layer) if is_external_table else gs_util.DEFAULT_DB_STORE_NAME
    gs_util.patch_feature_type(workspace, layer, auth=settings.LAYMAN_GS_AUTH, bbox=bbox, crs=crs,
                               store_name=store_name)
    wfs.clear_cache(workspace)

    if self.is_aborted():
        raise AbortedException
