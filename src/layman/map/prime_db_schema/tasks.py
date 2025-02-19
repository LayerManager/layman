from celery.utils.log import get_task_logger

from layman import celery_app
from layman.celery import AbortedException
from layman.common import empty_method_returns_true
from layman.util import XForwardedClass
from .util import ensure_internal_layers
from .. import util, MAP_TYPE
from ...common.prime_db_schema.publications import set_bbox

logger = get_task_logger(__name__)

JSON_EXTENT_CRS = 'EPSG:4326'
refresh_file_data_needed = empty_method_returns_true


@celery_app.task(
    name='layman.map.prime_db_schema.file_data.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_file_data(
        self,
        workspace,
        mapname,
        x_forwarded_headers,
        uuid,
):
    if self.is_aborted():
        raise AbortedException

    mapjson = util.get_map_file_json(uuid, workspace=workspace, adjust_urls=False)
    native_bbox = util.get_native_bbox_from_json(mapjson)
    crs = util.get_crs_from_json(mapjson)
    set_bbox(workspace, MAP_TYPE, mapname, native_bbox, crs, )

    x_forwarded_items = XForwardedClass.from_headers(x_forwarded_headers)
    map_layers = util.get_layers_from_json(mapjson, x_forwarded_items=x_forwarded_items)
    ensure_internal_layers(workspace, mapname, map_layers)

    if self.is_aborted():
        raise AbortedException
