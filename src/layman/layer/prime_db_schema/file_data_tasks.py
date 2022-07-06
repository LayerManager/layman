from celery.utils.log import get_task_logger

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

    info = layman_util.get_publication_info(username, LAYER_TYPE, layername, context={'keys': ['file', 'native_crs', 'db_table']})
    file_type = info['file']['file_type']
    crs = info['native_crs']
    db_table = info['db_table']['name']
    assert file_type == settings.FILE_TYPE_VECTOR
    bbox = db_get_bbox(username, db_table)

    if self.is_aborted():
        raise AbortedException

    set_bbox(username, LAYER_TYPE, layername, bbox, crs)

    if self.is_aborted():
        raise AbortedException
