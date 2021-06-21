from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman.common import empty_method_returns_true
from layman.layer.filesystem.input_file import get_layer_main_file_path
from layman import celery_app, util as layman_util, settings
from layman.http import LaymanError
from .. import db, LAYER_TYPE
from .table import delete_layer


logger = get_task_logger(__name__)

refresh_table_needed = empty_method_returns_true


@celery_app.task(
    name='layman.layer.db.table.refresh',
    bind=True,
    base=celery_app.AbortableTask
)
def refresh_table(
        self,
        username,
        layername,
        crs_id=None,
        ensure_user=False
):
    if ensure_user:
        db.ensure_workspace(username)
    if self.is_aborted():
        raise AbortedException

    file_type = layman_util.get_publication_info(username, LAYER_TYPE, layername, context={'keys': ['file']})['file']['file_type']
    if file_type != settings.FILE_TYPE_VECTOR:
        return

    if self.is_aborted():
        raise AbortedException

    main_filepath = get_layer_main_file_path(username, layername)
    process = db.import_layer_vector_file_async(username, layername, main_filepath, crs_id)
    while process.poll() is None and not self.is_aborted():
        pass
    if self.is_aborted():
        logger.info(f'terminating {username} {layername}')
        process.terminate()
        logger.info(f'terminating {username} {layername}')
        delete_layer(username, layername)
        raise AbortedException
    return_code = process.poll()
    if return_code != 0:
        pg_error = str(process.stdout.read())
        logger.error(f"STDOUT: {pg_error}")
        if "ERROR:  zero-length delimited identifier at or near" in pg_error:
            err_code = 28
        else:
            err_code = 11
        raise LaymanError(err_code, private_data=pg_error)
