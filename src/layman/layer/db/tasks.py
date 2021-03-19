from celery.utils.log import get_task_logger

from layman.celery import AbortedException
from layman.layer.filesystem.input_file import get_layer_main_file_path
from layman import celery_app
from layman.http import LaymanError
from .. import db
from .table import delete_layer


logger = get_task_logger(__name__)


def refresh_table_needed(username, layername, task_options):
    return True


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
    main_filepath = get_layer_main_file_path(username, layername)
    p = db.import_layer_vector_file_async(username, layername, main_filepath, crs_id)
    while p.poll() is None and not self.is_aborted():
        pass
    if self.is_aborted():
        logger.info(f'terminating {username} {layername}')
        p.terminate()
        logger.info(f'terminating {username} {layername}')
        delete_layer(username, layername)
        raise AbortedException
    return_code = p.poll()
    if return_code != 0:
        pg_error = str(p.stdout.read())
        logger.error(f"STDOUT: {pg_error}")
        if "ERROR:  zero-length delimited identifier at or near" in pg_error:
            err_code = 28
        else:
            err_code = 11
        raise LaymanError(err_code, private_data=pg_error)
