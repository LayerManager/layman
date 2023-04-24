from celery.utils.log import get_task_logger

from db import util as db_util
from layman.celery import AbortedException
from layman.common import empty_method_returns_true
from layman.common.prime_db_schema import publications
from layman import celery_app, util as layman_util, settings
from .. import LAYER_TYPE
from ..db import get_bbox as db_get_bbox, get_table_crs
from ..filesystem.gdal import get_bbox as gdal_get_bbox, get_crs as gdal_get_crs
from ...common.prime_db_schema.publications import set_bbox, set_geodata_type

logger = get_task_logger(__name__)

refresh_file_data_needed = empty_method_returns_true
refresh_wfs_wms_status_needed = empty_method_returns_true


@celery_app.task(
    name='layman.layer.prime_db_schema.file_data.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_file_data(
        self,
        username,
        layername,
):
    if self.is_aborted():
        raise AbortedException

    publ_info = layman_util.get_publication_info(username, LAYER_TYPE, layername, context={'keys': ['geodata_type', 'table_uri']})
    if publ_info['geodata_type'] == settings.GEODATA_TYPE_UNKNOWN:
        publ_info_file = layman_util.get_publication_info(username, LAYER_TYPE, layername, context={'keys': ['file']})
        geodata_type = publ_info_file['_file']['file_type']
        set_geodata_type(username, LAYER_TYPE, layername, geodata_type, )
    else:
        geodata_type = publ_info['geodata_type']

    if geodata_type == settings.GEODATA_TYPE_VECTOR:
        if not publ_info.get('_table_uri'):
            # We have to set file type into publications table before asking for table_uri,
            # because for compressed files sent with chunks file_type would be UNKNOWN and table_uri not set
            publ_info = layman_util.get_publication_info(username, LAYER_TYPE, layername, context={'keys': ['table_uri']})
        table_uri = publ_info['_table_uri']
        conn_cur = db_util.get_connection_cursor(db_uri_str=table_uri.db_uri_str)
        bbox = db_get_bbox(table_uri.schema, table_uri.table, conn_cur=conn_cur, column=table_uri.geo_column)
        crs = get_table_crs(table_uri.schema, table_uri.table, conn_cur=conn_cur, column=table_uri.geo_column, use_internal_srid=True)
    elif geodata_type == settings.GEODATA_TYPE_RASTER:
        bbox = gdal_get_bbox(username, layername)
        crs = gdal_get_crs(username, layername)
    else:
        raise NotImplementedError(f"Unknown geodata type: {geodata_type}")

    if self.is_aborted():
        raise AbortedException

    set_bbox(username, LAYER_TYPE, layername, bbox, crs, )

    if self.is_aborted():
        raise AbortedException


@celery_app.task(
    name='layman.layer.prime_db_schema.wfs_wms_status.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_wfs_wms_status(
        self,
        username,
        layername,
):
    if self.is_aborted():
        raise AbortedException

    publications.set_wfs_wms_status(username, LAYER_TYPE, layername, settings.EnumWfsWmsStatus.AVAILABLE)

    if self.is_aborted():
        raise AbortedException
