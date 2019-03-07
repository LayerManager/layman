import time

from celery.utils.log import get_task_logger

from layman.layer.filesystem.input_files import get_layer_main_file_path
from layman import celery_app
from layman.http import LaymanError
from . import import_layer_vector_file_async, ensure_user_schema
from .table import delete_layer

logger = get_task_logger(__name__)

# @celery_app.task
# def import_layer_vector_file(username, layername, main_filepath, crs_id):
#     return db.import_layer_vector_file(username, layername, main_filepath,
#                                        crs_id)


@celery_app.task(bind=True, base=celery_app.AbortableTask)
def long(self, username, layername, main_filepath, crs_id):

    logger.info('Hello ...')
    for i in range(6):
        if self.is_aborted():
            logger.warning('ENDING TASK '+long.request.id)
            return
        time.sleep(1)

    logger.info('... world!')


@celery_app.task(
    name='layman.layer.db.import_layer_vector_file',
    bind=True,
    base=celery_app.AbortableTask
)
def import_layer_vector_file(
        self,
        username,
        layername,
        crs_id=None,
        ensure_user=False
    ):
    if ensure_user:
        ensure_user_schema(username)
    if self.is_aborted():
        return
    main_filepath = get_layer_main_file_path(username, layername)
    p = import_layer_vector_file_async(username, layername, main_filepath,
                                    crs_id)
    while p.poll() is None and not self.is_aborted():
        pass
    if self.is_aborted():
        logger.info(f'aborting {username} {layername}')
        p.terminate()
        logger.info(f'aborted {username} {layername}')
        delete_layer(username, layername)
    else:
        # logger.info('STDOUT', p.stdout.read())
        return_code = p.poll()
        if return_code != 0:
            raise LaymanError(11)
