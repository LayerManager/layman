import time
# import layman.db as db
from layman import celery_app
from celery.contrib.abortable import AbortableTask
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

# @celery_app.task
# def import_layer_vector_file(username, layername, main_filepath, crs_id):
#     return db.import_layer_vector_file(username, layername, main_filepath,
#                                        crs_id)


@celery_app.task(bind=True, base=AbortableTask)
def long(self, username, layername, main_filepath, crs_id):

    logger.info('Hello ...')
    for i in range(6):
        if self.is_aborted():
            logger.warning('ENDING TASK '+long.request.id)
            return
        time.sleep(1)

    logger.info('... world!')
