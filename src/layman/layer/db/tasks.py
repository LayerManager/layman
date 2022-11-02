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
):
    db.ensure_workspace(workspace)
    if self.is_aborted():
        raise AbortedException

    publ_info = layman_util.get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': ['file']})
    file_type = publ_info['file']['file_type']
    if file_type == settings.FILE_TYPE_RASTER:
        return
    if file_type != settings.FILE_TYPE_VECTOR:
        raise NotImplementedError(f"Unknown file type: {file_type}")

    if self.is_aborted():
        raise AbortedException

    main_filepaths = list(path['gdal'] for path in publ_info['_file']['paths'].values())
    assert len(main_filepaths) == 1
    main_filepath = main_filepaths[0]
    table_name = db.get_table_name(workspace, layername)
    process = db.import_layer_vector_file_async(workspace, table_name, main_filepath, crs_id)
    while process.poll() is None and not self.is_aborted():
        pass
    if self.is_aborted():
        logger.info(f'terminating {workspace} {layername}')
        process.terminate()
        logger.info(f'terminating {workspace} {layername}')
        table.delete_layer(workspace, layername)
        raise AbortedException
    return_code = process.poll()
    output = process.stdout.read()
    if return_code != 0 or output:
        info = table.get_layer_info(workspace, layername)
        if not info:
            pg_error = str(output)
            logger.error(f"STDOUT: {pg_error}")
            if "ERROR:  zero-length delimited identifier at or near" in pg_error:
                err_code = 28
            else:
                err_code = 11
            raise LaymanError(err_code, private_data=pg_error)

    crs = db.get_crs(workspace, table_name)
    if crs_def.CRSDefinitions[crs].srid:
        table.set_layer_srid(workspace, table_name, crs_def.CRSDefinitions[crs].srid)
