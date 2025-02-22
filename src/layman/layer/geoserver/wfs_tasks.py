from geoserver import util as gs_util
from layman import celery_app, settings
from layman.celery import AbortedException
from layman.layer.layer_class import Layer
from . import wfs
from .util import get_db_store_name
from .. import geoserver

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

    layer_data = Layer(layer_tuple=(workspace, layer))

    if layer_data.geodata_type == settings.GEODATA_TYPE_RASTER:
        return
    if layer_data.geodata_type != settings.GEODATA_TYPE_VECTOR:
        raise NotImplementedError(f"Unknown geodata type: {layer_data.geodata_type}")

    bbox = geoserver.get_layer_bbox_by_layer(layer=layer_data)
    store_name = get_db_store_name(uuid=layer_data.uuid, db_schema=workspace, original_data_source=layer_data.original_data_source)
    gs_layername = layer_data.gs_names.wfs
    gs_util.patch_feature_type(gs_layername.workspace, gs_layername.name, auth=settings.LAYMAN_GS_AUTH, bbox=bbox, crs=layer_data.native_crs,
                               store_name=store_name)
    wfs.clear_cache()

    if self.is_aborted():
        raise AbortedException
