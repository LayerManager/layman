from . import thumbnail
from layman import celery_app
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@celery_app.task(
    name='layman.filesystem.thumbnail.generate_layer_thumbnail',
    bind=True,
    base=celery_app.AbortableTask
)
def generate_layer_thumbnail(self, username, layername):
    thumbnail.generate_layer_thumbnail(username, layername)

    if self.is_aborted():
        print('aborting generate_layer_thumbnail', username, layername)
        thumbnail.delete_layer(username, layername)

