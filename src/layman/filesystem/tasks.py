import time
from layman.settings import *
from . import thumbnail
from . import input_files
from layman import celery_app
from layman.http import LaymanError
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)



@celery_app.task(
    name='layman.filesystem.input_files.wait_for_upload',
    bind=True,
    base=celery_app.AbortableTask
)
def wait_for_upload(self, username, layername, check_crs=True):
    if self.is_aborted():
        return
    last_change = time.time()
    num_files_saved = 0
    num_chunks_saved = 0
    chunk_info = input_files.layer_file_chunk_info(username, layername)

    logger.debug(f'chunk_info {str(chunk_info)}')
    while not chunk_info[0]:
        if time.time() - last_change > UPLOAD_MAX_INACTIVITY_TIME:
            logger.info(
                f'UPLOAD_MAX_INACTIVITY_TIME reached {username}.{layername}')
            input_files.delete_layer(username, layername)
            raise LaymanError(22)
        time.sleep(0.5)
        if self.is_aborted():
            logger.info(f'Aborting for layer {username}.{layername}')
            input_files.delete_layer(username, layername)
            logger.info(f'Aborted for layer {username}.{layername}')
            return

        chunk_info = input_files.layer_file_chunk_info(username, layername)
        logger.debug(f'chunk_info {str(chunk_info)}')
        if num_files_saved != chunk_info[1] \
                or num_chunks_saved != chunk_info[2]:
            last_change = time.time()
            num_files_saved = chunk_info[1]
            num_chunks_saved = chunk_info[2]
    else:
        logger.info(f'Layer chunks uploaded {username}.{layername}')

    if check_crs:
        main_filepath = input_files.get_layer_main_file_path(username, layername)
        input_files.check_layer_crs(main_filepath)


@celery_app.task(
    name='layman.filesystem.thumbnail.generate_layer_thumbnail',
    bind=True,
    base=celery_app.AbortableTask
)
def generate_layer_thumbnail(self, username, layername):
    if self.is_aborted():
        return
    thumbnail.generate_layer_thumbnail(username, layername)

    if self.is_aborted():
        thumbnail.delete_layer(username, layername)

