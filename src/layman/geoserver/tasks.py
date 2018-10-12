from . import wms
from . import wfs
from . import sld
from layman import geoserver
from layman import celery_app
from celery.contrib.abortable import AbortableTask
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@celery_app.task(
    name='layman.geoserver.publish_layer_from_db',
    bind=True,
    base=AbortableTask
)
def publish_layer_from_db(self, username, layername, description, title):
    geoserver.publish_layer_from_db(username, layername, description, title)

    if self.is_aborted():
        print('aborting publish_layer_from_db', username, layername)
        wms.delete_layer(username, layername)
        wfs.delete_layer(username, layername)

@celery_app.task(
    name='layman.geoserver.sld.create_layer_style',
    bind=True,
    base=AbortableTask
)
def create_layer_style(self, username, layername):
    sld.create_layer_style(username, layername)

    if self.is_aborted():
        print('aborting create_layer_style', username, layername)
        sld.delete_layer(username, layername)

