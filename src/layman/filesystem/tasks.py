import time
from . import thumbnail
from . import input_files
from layman import celery_app
from layman.http import LaymanError
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

MAX_INACTIVITY_TIME = 10 # 10 seconds
# MAX_INACTIVITY_TIME = 5 * 60 # 5 minutes


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

    logger.debug('chunk_info {}'.format(str(chunk_info)))
    while not chunk_info[0] and \
                            time.time() - last_change <= MAX_INACTIVITY_TIME:
        time.sleep(0.5)
        if self.is_aborted():
            logger.info('Aborting for layer {}.{}'.format(username, layername))
            input_files.delete_layer(username, layername)
            logger.info('Aborted for layer {}.{}'.format(username, layername))
            return

        chunk_info = input_files.layer_file_chunk_info(username, layername)
        logger.debug('chunk_info {}'.format(str(chunk_info)))
        if num_files_saved != chunk_info[1] \
                or num_chunks_saved != chunk_info[2]:
            last_change = time.time()
            num_files_saved = chunk_info[1]
            num_chunks_saved = chunk_info[2]
    if time.time() - last_change > MAX_INACTIVITY_TIME:
        raise LaymanError(22)
    else:
        logger.info('Layer chunks uploaded {}.{}'.format(username, layername))

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

