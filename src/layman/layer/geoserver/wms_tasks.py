from geoserver import util as gs_util
from layman import celery_app, settings, util as layman_util
from layman.celery import AbortedException
from . import wms
from .. import geoserver, LAYER_TYPE

headers_json = geoserver.headers_json


@celery_app.task(
    name='layman.layer.geoserver.wms.patch_after_feature_change',
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
    if file_type == settings.FILE_TYPE_VECTOR:
        bbox = geoserver.get_layer_bbox(workspace, layer)
        geoserver_workspace = wms.get_geoserver_workspace(workspace)
        style_type = layman_util.get_publication_info(workspace, LAYER_TYPE, layer, context={'keys': ['style_type'], })['style_type']
        if style_type == 'sld':
            gs_util.patch_feature_type(geoserver_workspace, layer, auth=settings.LAYMAN_GS_AUTH, bbox=bbox)
        elif style_type == 'qml':
            gs_util.patch_wms_layer(geoserver_workspace, layer, auth=settings.LAYMAN_GS_AUTH, bbox=bbox)

    wms.clear_cache(workspace)

    if self.is_aborted():
        raise AbortedException
