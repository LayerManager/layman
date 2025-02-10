from geoserver import util as gs_util
from layman import celery_app, settings, util as layman_util, names
from layman.celery import AbortedException
from . import wfs
from .util import get_db_store_name
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
                                            context={'keys': ['geodata_type', 'native_crs', 'original_data_source', 'uuid', ]})
    uuid = info['uuid']
    geodata_type = info['geodata_type']
    if geodata_type == settings.GEODATA_TYPE_RASTER:
        return
    if geodata_type != settings.GEODATA_TYPE_VECTOR:
        raise NotImplementedError(f"Unknown geodata type: {geodata_type}")

    bbox = geoserver.get_layer_bbox_by_uuid(uuid=uuid)
    crs = info['native_crs']
    original_data_source = info['original_data_source']
    store_name = get_db_store_name(uuid=uuid, db_schema=workspace, original_data_source=original_data_source)
    gs_layername = names.get_layer_names_by_source(uuid=uuid).wfs
    gs_util.patch_feature_type(gs_layername.workspace, gs_layername.name, auth=settings.LAYMAN_GS_AUTH, bbox=bbox, crs=crs,
                               store_name=store_name)
    wfs.clear_cache()

    if self.is_aborted():
        raise AbortedException
