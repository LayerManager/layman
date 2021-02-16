from celery.utils.log import get_task_logger
from flask import current_app as app

from layman import settings, celery_app
from layman.celery import AbortedException
from layman.layer import qgis, util as layer_util
from layman.layer.filesystem import input_style
from . import util, wms
from .. import db


logger = get_task_logger(__name__)


def refresh_wms_needed(username, layername, task_options):
    return True


@celery_app.task(
    name='layman.layer.qgis.wms.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_wms(
        self,
        username,
        layername,
        store_in_geoserver
):
    if self.is_aborted():
        raise AbortedException

    if not store_in_geoserver:
        info = layer_util.get_layer_info(username, layername)
        uuid = info['uuid']
        qgis.ensure_layer_dir(username, layername)
        with app.app_context():
            layer_bbox = db.get_bbox(username, layername)
        layer_bbox = layer_bbox or settings.LAYMAN_DEFAULT_OUTPUT_BBOX
        qml_path = input_style.get_file_path(username, layername)
        layer_qml = util.fill_layer_template(username, layername, uuid, layer_bbox, qml_path)
        qgs_str = util.fill_project_template(username, layername, uuid, layer_qml, settings.LAYMAN_OUTPUT_SRS_LIST, layer_bbox)
        with open(wms.get_layer_file_path(username, layername), "w") as qgs_file:
            print(qgs_str, file=qgs_file)

    if self.is_aborted():
        wms.delete_layer(username, layername)
        raise AbortedException
