import crs as crs_def
from geoserver import util as gs_util
from layman import celery_app, settings, util as layman_util
from layman.common import bbox as bbox_util
from layman.celery import AbortedException
from . import wms, get_external_db_store_name
from .. import geoserver, LAYER_TYPE

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

    publ_info = layman_util.get_publication_info(workspace, LAYER_TYPE, layer,
                                                 context={'keys': ['geodata_type', 'original_data_source']})
    geodata_type = publ_info['geodata_type']
    if geodata_type == settings.GEODATA_TYPE_VECTOR:
        bbox = geoserver.get_layer_bbox(workspace, layer)
        geoserver_workspace = wms.get_geoserver_workspace(workspace)
        info = layman_util.get_publication_info(workspace, LAYER_TYPE, layer, context={'keys': ['style_type', 'native_crs', ], })
        style_type = info['_style_type']
        crs = info['native_crs']
        lat_lon_bbox = bbox_util.transform(bbox, crs, crs_def.EPSG_4326)
        if style_type == 'sld':
            original_data_source = info['original_data_source']
            store_name = get_external_db_store_name(layer) if original_data_source == settings.EnumOriginalDataSource.TABLE.value else gs_util.DEFAULT_DB_STORE_NAME
            gs_util.patch_feature_type(geoserver_workspace, layer, auth=settings.LAYMAN_GS_AUTH, bbox=bbox, crs=crs,
                                       lat_lon_bbox=lat_lon_bbox, store_name=store_name)
        elif style_type == 'qml':
            gs_util.patch_wms_layer(geoserver_workspace, layer, auth=settings.LAYMAN_GS_AUTH, bbox=bbox, crs=crs, lat_lon_bbox=lat_lon_bbox)
    elif geodata_type != settings.GEODATA_TYPE_RASTER:
        raise NotImplementedError(f"Unknown geodata type: {geodata_type}")

    wms.clear_cache(workspace)

    if self.is_aborted():
        raise AbortedException
