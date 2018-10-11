import time
# import layman.db as db
from .table import delete_layer
from .__init__ import import_layer_vector_file_async
from layman import celery_app
from layman.http import LaymanError
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


@celery_app.task(
    name='layman.db.import_layer_vector_file',
    bind=True,
    base=AbortableTask
)
def import_layer_vector_file(self, username, layername, main_filepath, crs_id):
    p = import_layer_vector_file_async(username, layername, main_filepath,
                                    crs_id)
    while p.poll() is None and not self.is_aborted():
        pass
    if self.is_aborted():
        print('aborting import_layer_vector_file_async', username, layername)
        p.terminate()
        delete_layer(username, layername)
    else:
        # logger.info('STDOUT', p.stdout.read())
        return_code = p.poll()
        if return_code != 0:
            raise LaymanError(11)
