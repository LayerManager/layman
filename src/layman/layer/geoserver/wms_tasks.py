import crs as crs_def
from geoserver import util as gs_util
from layman import celery_app, settings
from layman.common import bbox as bbox_util
from layman.celery import AbortedException
from layman.layer.layer_class import Layer
from . import wms
from .util import get_db_store_name, get_layer_bbox

headers_json = gs_util.headers_json


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

    layer_data = Layer(layer_tuple=(workspace, layer))

    if layer_data.geodata_type == settings.GEODATA_TYPE_VECTOR:
        bbox = get_layer_bbox(layer=layer_data)
        wms_layername = layer_data.gs_ids.wms
        lat_lon_bbox = bbox_util.transform(bbox, layer_data.native_crs, crs_def.EPSG_4326)
        if layer_data.style_type == 'sld':
            store_name = get_db_store_name(uuid=layer_data.uuid,
                                           original_data_source=layer_data.original_data_source.value)
            gs_util.patch_feature_type(wms_layername.workspace, wms_layername.name, auth=settings.LAYMAN_GS_AUTH, bbox=bbox, crs=layer_data.native_crs,
                                       lat_lon_bbox=lat_lon_bbox, store_name=store_name)
        elif layer_data.style_type == 'qml':
            gs_util.patch_wms_layer(wms_layername.workspace, wms_layername.name, auth=settings.LAYMAN_GS_AUTH, bbox=bbox, crs=layer_data.native_crs, lat_lon_bbox=lat_lon_bbox)
        wms.clear_cache()
    elif layer_data.style_type != settings.GEODATA_TYPE_RASTER:
        raise NotImplementedError(f"Unknown geodata type: {layer_data.geodata_type}")

    if self.is_aborted():
        raise AbortedException
