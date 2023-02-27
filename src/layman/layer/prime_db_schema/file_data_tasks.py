from celery.utils.log import get_task_logger

from db import util as db_util
from layman.celery import AbortedException
from layman import celery_app, util as layman_util, settings
from .. import LAYER_TYPE
from ..db import get_bbox as db_get_bbox
from ...common.prime_db_schema.publications import set_bbox

logger = get_task_logger(__name__)


@celery_app.task(
    name='layman.layer.prime_db_schema.file_data.patch_after_feature_change',
    bind=True,
    base=celery_app.AbortableTask
)
def patch_after_feature_change(
        self,
        username,
        layername,
):
    if self.is_aborted():
        raise AbortedException

    info = layman_util.get_publication_info(username, LAYER_TYPE, layername,
                                            context={'keys': ['geodata_type', 'native_crs', 'table_uri']})
    geodata_type = info['geodata_type']
    crs = info['native_crs']
    assert geodata_type == settings.GEODATA_TYPE_VECTOR

    table_uri = info['_table_uri']
    conn_cur = db_util.get_connection_cursor(db_uri_str=table_uri.db_uri_str)
    bbox = db_get_bbox(table_uri.schema, table_uri.table, conn_cur=conn_cur, column=table_uri.geo_column)

    if self.is_aborted():
        raise AbortedException

    set_bbox(username, LAYER_TYPE, layername, bbox, crs)

    if self.is_aborted():
        raise AbortedException
