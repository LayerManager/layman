from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman.common import empty_method_returns_true
from layman import celery_app, util as layman_util, settings
from .. import LAYER_TYPE
from ..db import get_bbox as db_get_bbox, get_crs as db_get_crs
from ..filesystem.gdal import get_bbox as gdal_get_bbox, get_crs as gdal_get_crs
from ...common.prime_db_schema.publications import set_bbox

logger = get_task_logger(__name__)

refresh_bbox_needed = empty_method_returns_true


@celery_app.task(
    name='layman.layer.prime_db_schema.bbox.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_bbox(
        self,
        username,
        layername,
):
    if self.is_aborted():
        raise AbortedException

    publ_info = layman_util.get_publication_info(username, LAYER_TYPE, layername, context={'keys': ['file', 'db_table']})
    file_type = publ_info['file']['file_type']
    if file_type == settings.FILE_TYPE_VECTOR:
        table_name = publ_info['db_table']['name']
        bbox = db_get_bbox(username, table_name)
        crs = db_get_crs(username, table_name)
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
