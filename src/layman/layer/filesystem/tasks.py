import os
import time
import tempfile

from celery.utils.log import get_task_logger

from layman import celery_app, settings, util as layman_util
from layman.celery import AbortedException
from layman.common import empty_method_returns_true
from layman.http import LaymanError
from . import input_file, input_chunk, thumbnail, gdal
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
def refresh_input_chunk(self, workspace, layername, check_crs=True, overview_resampling='', enable_more_main_files=False):
    if self.is_aborted():
        raise AbortedException
    last_change = time.time()
    num_files_saved = 0
    num_chunks_saved = 0
    chunk_info = input_chunk.layer_file_chunk_info(workspace, layername)

    logger.debug(f'chunk_info {str(chunk_info)}')
    while not chunk_info[0]:
        if time.time() - last_change > settings.UPLOAD_MAX_INACTIVITY_TIME:
            logger.info(
                f'UPLOAD_MAX_INACTIVITY_TIME reached {workspace}.{layername}')
            input_file.delete_layer(workspace, layername)
            raise LaymanError(22)
        time.sleep(0.5)
        if self.is_aborted():
            logger.info(f'Aborting for layer {workspace}.{layername}')
            input_file.delete_layer(workspace, layername)
            logger.info(f'Aborted for layer {workspace}.{layername}')
            raise AbortedException

        chunk_info = input_chunk.layer_file_chunk_info(workspace, layername)
        logger.debug(f'chunk_info {str(chunk_info)}')
        if num_files_saved != chunk_info[1] \
                or num_chunks_saved != chunk_info[2]:
            last_change = time.time()
            num_files_saved = chunk_info[1]
            num_chunks_saved = chunk_info[2]
    logger.info(f'Layer chunks uploaded {workspace}.{layername}')

    input_files = input_file.get_layer_input_files(workspace, layername)
    input_file.check_filenames(workspace, layername, input_files, check_crs, ignore_existing_files=True, enable_more_main_files=enable_more_main_files)

    main_filepaths = layman_util.get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': ['file']})['_file']['gdal_paths']
    for main_filepath in main_filepaths:
        input_file.check_main_file(main_filepath, check_crs=check_crs, overview_resampling=overview_resampling)

    file_type = input_file.get_file_type(input_files.raw_or_archived_main_file_path)
    style_type_for_check = layman_util.get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': ['style_type']})['_style_type']
    if file_type == settings.FILE_TYPE_RASTER and style_type_for_check == 'qml':
        raise LaymanError(48, f'Raster layers are not allowed to have QML style.')


@celery_app.task(
    name='layman.layer.filesystem.gdal.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_gdal(self, workspace, layername, crs_id=None, overview_resampling=None, normalize_filenames=True):
    def finish_gdal_process(process):
        if self.is_aborted():
            logger.info(f'terminating GDAL process workspace.layer={workspace}.{layername}')
            process.terminate()
            logger.info(f'terminated GDAL process workspace.layer={workspace}.{layername}')
            gdal.delete_layer(workspace, layername)
            raise AbortedException
        return_code = process.poll()
        if return_code != 0:
            gdal_error = str(process.stdout.read())
            logger.error(f"STDOUT: {gdal_error}")
            raise LaymanError(50, private_data=gdal_error)

    if self.is_aborted():
        raise AbortedException
    layer_info = layman_util.get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': ['file']})
    file_type = layer_info['file']['file_type']
    if file_type != settings.FILE_TYPE_RASTER:
        return

    gdal.ensure_normalized_raster_layer_dir(workspace, layername)

    if self.is_aborted():
        raise AbortedException

    input_paths = layer_info['_file']['gdal_paths']
    for input_path in input_paths:
        vrt_file_path = gdal.create_vrt_file_if_needed(input_path)
        tmp_vrt_file = tempfile.mkstemp(suffix='.vrt')[1]
        process = gdal.normalize_raster_file_async(vrt_file_path or input_path, crs_id, output_file=tmp_vrt_file)
        while process.poll() is None and not self.is_aborted():
            pass
        finish_gdal_process(process)

        source_file = f'{layername}.tif' if normalize_filenames else input_path
        normalize_file_path = gdal.get_normalized_raster_layer_main_filepath(workspace, layername, source_file=source_file, )
        process = gdal.compress_raster_file_async(output_file=normalize_file_path, file_to_compress=tmp_vrt_file, )
        while process.poll() is None and not self.is_aborted():
            pass
        if vrt_file_path:
            try:
                os.remove(vrt_file_path)
            except OSError:
                pass
        try:
            os.remove(tmp_vrt_file)
        except OSError:
            pass
        finish_gdal_process(process)

        process = gdal.add_overview_async(filepath=normalize_file_path, overview_resampling=overview_resampling, )
        while process.poll() is None and not self.is_aborted():
            pass
        finish_gdal_process(process)


@celery_app.task(
    name='layman.layer.filesystem.thumbnail.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_thumbnail(self, workspace, layername):
    if self.is_aborted():
        raise AbortedException
    thumbnail.generate_layer_thumbnail(workspace, layername)

    if self.is_aborted():
        thumbnail.delete_layer(workspace, layername)
        raise AbortedException
