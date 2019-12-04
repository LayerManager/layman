import time

from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman import celery_app
from layman.http import LaymanError
from layman import settings
from . import input_file, input_chunk, thumbnail

logger = get_task_logger(__name__)


def refresh_input_chunk_needed(username, layername, task_options):
    return True


@celery_app.task(
    name='layman.layer.filesystem.input_chunk.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_input_chunk(self, username, layername, check_crs=True):
    if self.is_aborted():
        raise AbortedException
    last_change = time.time()
    num_files_saved = 0
    num_chunks_saved = 0
    chunk_info = input_chunk.layer_file_chunk_info(username, layername)

    logger.debug(f'chunk_info {str(chunk_info)}')
    while not chunk_info[0]:
        if time.time() - last_change > settings.UPLOAD_MAX_INACTIVITY_TIME:
            logger.info(
                f'UPLOAD_MAX_INACTIVITY_TIME reached {username}.{layername}')
            input_file.delete_layer(username, layername)
            raise LaymanError(22)
        time.sleep(0.5)
        if self.is_aborted():
            logger.info(f'Aborting for layer {username}.{layername}')
            input_file.delete_layer(username, layername)
            logger.info(f'Aborted for layer {username}.{layername}')
            raise AbortedException

        chunk_info = input_chunk.layer_file_chunk_info(username, layername)
        logger.debug(f'chunk_info {str(chunk_info)}')
        if num_files_saved != chunk_info[1] \
                or num_chunks_saved != chunk_info[2]:
            last_change = time.time()
            num_files_saved = chunk_info[1]
            num_chunks_saved = chunk_info[2]
    else:
        logger.info(f'Layer chunks uploaded {username}.{layername}')

    if check_crs:
        main_filepath = input_file.get_layer_main_file_path(username, layername)
        input_file.check_layer_crs(main_filepath)


def refresh_thumbnail_needed(username, layername, task_options):
    return True


@celery_app.task(
    name='layman.layer.filesystem.thumbnail.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_thumbnail(self, username, layername):
    if self.is_aborted():
        raise AbortedException
    thumbnail.generate_layer_thumbnail(username, layername)

    if self.is_aborted():
        thumbnail.delete_layer(username, layername)
        raise AbortedException

