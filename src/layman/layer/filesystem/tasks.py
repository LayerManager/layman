import time

from celery.utils.log import get_task_logger

from layman import celery_app, settings, util as layman_util
from layman.celery import AbortedException
from layman.common import empty_method_returns_true
from layman.http import LaymanError
from . import input_file, input_chunk, thumbnail, util, gdal
from .. import LAYER_TYPE

logger = get_task_logger(__name__)

refresh_input_chunk_needed = empty_method_returns_true
refresh_thumbnail_needed = empty_method_returns_true
refresh_gdal_needed = empty_method_returns_true


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
    logger.info(f'Layer chunks uploaded {username}.{layername}')

    if check_crs:
        main_filepath = input_file.get_layer_main_file_path(username, layername)
        input_file.check_layer_crs(main_filepath)


@celery_app.task(
    name='layman.layer.filesystem.gdal.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_gdal(self, username, layername, crs_id=None):
    if self.is_aborted():
        raise AbortedException
    layer_info = layman_util.get_publication_info(username, LAYER_TYPE, layername, context={'keys': ['file']})
    file_type = layer_info['file']['file_type']
    if file_type != settings.FILE_TYPE_RASTER:
        return

    util.ensure_normalized_raster_layer_dir(username, layername)

    if self.is_aborted():
        raise AbortedException

    input_path = layer_info['_file']['path']
    process = gdal.normalize_raster_file_async(username, layername, input_path, crs_id)
    while process.poll() is None and not self.is_aborted():
        pass
    if self.is_aborted():
        logger.info(f'terminating GDAL process workspace.layer={username}.{layername}')
        process.terminate()
        logger.info(f'terminated GDAL process workspace.layer={username}.{layername}')
        gdal.delete_layer(username, layername)
        raise AbortedException
    return_code = process.poll()
    if return_code != 0:
        gdal_error = str(process.stdout.read())
        logger.error(f"STDOUT: {gdal_error}")
        raise LaymanError(50, private_data=gdal_error)


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
