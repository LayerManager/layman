from celery.utils.log import get_task_logger

from db import util as db_util
from layman.celery import AbortedException
from layman.common import empty_method_returns_true
from layman import celery_app, util as layman_util, settings
from .. import LAYER_TYPE
from ..db import get_bbox as db_get_bbox, get_crs as db_get_crs
from ..filesystem.gdal import get_bbox as gdal_get_bbox, get_crs as gdal_get_crs
from ...common.prime_db_schema.publications import set_bbox, set_file_type

logger = get_task_logger(__name__)

refresh_file_data_needed = empty_method_returns_true


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

    publ_info = layman_util.get_publication_info(username, LAYER_TYPE, layername, context={'keys': ['file_type', 'table_uri']})
    if publ_info['_file_type'] == settings.FILE_TYPE_UNKNOWN:
        publ_info_file = layman_util.get_publication_info(username, LAYER_TYPE, layername, context={'keys': ['file']})
        file_type = publ_info_file['file']['file_type']
        set_file_type(username, LAYER_TYPE, layername, file_type, )
    else:
        file_type = publ_info['_file_type']

    if file_type == settings.FILE_TYPE_VECTOR:
        if not publ_info.get('_table_uri'):
            # We have to set file type into publications table before asking for table_uri,
            # because for compressed files sent with chunks file_type would be UNKNOWN and table_uri not set
            publ_info = layman_util.get_publication_info(username, LAYER_TYPE, layername, context={'keys': ['table_uri']})
        table_uri = publ_info['_table_uri']
        conn_cur = db_util.create_connection_cursor(db_uri_str=table_uri.db_uri_str)
        bbox = db_get_bbox(table_uri.schema, table_uri.table, conn_cur=conn_cur, column=table_uri.geo_column)
        crs = db_get_crs(table_uri.schema, table_uri.table, conn_cur=conn_cur, column=table_uri.geo_column)
    elif file_type == settings.FILE_TYPE_RASTER:
        bbox = gdal_get_bbox(username, layername)
        crs = gdal_get_crs(username, layername)
    else:
        raise NotImplementedError(f"Unknown file type: {file_type}")

    if self.is_aborted():
        raise AbortedException

    set_bbox(username, LAYER_TYPE, layername, bbox, crs, )

    if self.is_aborted():
        raise AbortedException
