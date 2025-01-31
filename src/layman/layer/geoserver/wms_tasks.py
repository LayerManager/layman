import crs as crs_def
from geoserver import util as gs_util
from layman import celery_app, settings, util as layman_util, names
from layman.common import bbox as bbox_util
from layman.celery import AbortedException
from . import wms, get_external_db_store_name, get_internal_db_store_name
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
                                                 context={'keys': ['geodata_type', 'original_data_source', 'uuid', ]})
    geodata_type = publ_info['geodata_type']
    if geodata_type == settings.GEODATA_TYPE_VECTOR:
        uuid = publ_info['uuid']
        bbox = geoserver.get_layer_bbox_by_uuid(uuid=uuid)
        wms_layername = names.get_layer_names_by_source(uuid=uuid).wms
        info = layman_util.get_publication_info_by_uuid(uuid, context={'keys': ['style_type', 'native_crs', ], })
        style_type = info['_style_type']
        crs = info['native_crs']
        lat_lon_bbox = bbox_util.transform(bbox, crs, crs_def.EPSG_4326)
        if style_type == 'sld':
            original_data_source = info['original_data_source']
            store_name = get_external_db_store_name(uuid=info['uuid']) if original_data_source == settings.EnumOriginalDataSource.TABLE.value else get_internal_db_store_name(db_schema=workspace)
            gs_util.patch_feature_type(wms_layername.workspace, wms_layername.name, auth=settings.LAYMAN_GS_AUTH, bbox=bbox, crs=crs,
                                       lat_lon_bbox=lat_lon_bbox, store_name=store_name)
        elif style_type == 'qml':
            gs_util.patch_wms_layer(wms_layername.workspace, wms_layername.name, auth=settings.LAYMAN_GS_AUTH, bbox=bbox, crs=crs, lat_lon_bbox=lat_lon_bbox)
        wms.clear_cache()
    elif geodata_type != settings.GEODATA_TYPE_RASTER:
        raise NotImplementedError(f"Unknown geodata type: {geodata_type}")

    if self.is_aborted():
        raise AbortedException
