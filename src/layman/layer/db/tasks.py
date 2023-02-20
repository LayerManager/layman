from celery.utils.log import get_task_logger

import crs as crs_def
from layman.celery import AbortedException
from layman.common import empty_method_returns_true
from layman import celery_app, util as layman_util, settings
from layman.http import LaymanError
from . import table
from .. import db, LAYER_TYPE


logger = get_task_logger(__name__)

refresh_table_needed = empty_method_returns_true


@celery_app.task(
    name='layman.layer.db.table.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_table(
        self,
        workspace,
        layername,
        crs_id=None,
        original_data_source=settings.EnumOriginalDataSource.FILE.value,
):
    db.ensure_workspace(workspace)
    if self.is_aborted():
        raise AbortedException

    if original_data_source == settings.EnumOriginalDataSource.TABLE.value:
        return
    publ_info = layman_util.get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': ['file']})
    file_type = publ_info['file']['file_type']
    if file_type == settings.GEODATA_TYPE_RASTER:
        return
    if file_type != settings.GEODATA_TYPE_VECTOR:
        raise NotImplementedError(f"Unknown file type: {file_type}")

    if self.is_aborted():
        raise AbortedException

    main_filepaths = list(path['gdal'] for path in publ_info['_file']['paths'].values())
    assert len(main_filepaths) == 1
    main_filepath = main_filepaths[0]
    table_name = db.get_internal_table_name(workspace, layername)

    for try_num in [1, 2]:
        if try_num == 1:
            processes = [db.import_layer_vector_file_async(workspace, table_name, main_filepath, crs_id)]
        elif try_num == 2:
            processes = db.import_layer_vector_file_async_with_iconv(workspace, table_name, main_filepath, crs_id)
        process = processes[-1]
        stdout, stderr = process.communicate()
        return_code = process.poll()
        if self.is_aborted():
            logger.info(f'terminating {workspace} {layername}')
            for proc in processes:
                proc.terminate()
            logger.info(f'deleting {workspace} {layername}')
            table.delete_layer(workspace, layername)
            raise AbortedException
        if return_code != 0 or stdout or stderr:
            info = table.get_layer_info(workspace, layername)
            if not info:
                str_error = str(stderr)
                str_out = str(stdout)
                logger.error(f"STDOUT: {str(stdout)}")
                logger.error(f"STDERR: {str_error}")
                if "ERROR:  zero-length delimited identifier at or near" in str_out:
                    err_code = 28
                elif 'ERROR:  invalid byte sequence for encoding "UTF8":' in str_out:
                    continue
                else:
                    err_code = 11
                raise LaymanError(err_code, private_data=str_error)
        break

    crs = db.get_crs(workspace, table_name)
    if crs_def.CRSDefinitions[crs].srid:
        table.set_layer_srid(workspace, table_name, crs_def.CRSDefinitions[crs].srid)
