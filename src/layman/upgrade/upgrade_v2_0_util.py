import os
import glob
import inspect
import traceback
import logging

from layman.layer.filesystem import util as file_util
from layman.layer import LAYER_TYPE
import layman_settings as settings
from geoserver import util as gs_util


logger = logging.getLogger(__name__)


def delete_layer_from_geoserver_v1_23(layername, workspace):
    # geoserver sld
    gs_wms_workspace = f"{workspace}_wms"
    gs_util.delete_workspace_style(gs_wms_workspace, layername, auth=settings.LAYMAN_GS_AUTH)
    # geoserver wms
    gs_util.delete_feature_type(gs_wms_workspace, layername, settings.LAYMAN_GS_AUTH, store='postgresql')
    gs_util.delete_feature_type(gs_wms_workspace, layername, settings.LAYMAN_GS_AUTH, store=f'external_db_{layername}')
    gs_util.delete_wms_layer(gs_wms_workspace, layername, settings.LAYMAN_GS_AUTH)
    gs_util.delete_wms_store(gs_wms_workspace, settings.LAYMAN_GS_AUTH, f"qgis_{layername}")
    gs_util.delete_coverage_store(gs_wms_workspace, settings.LAYMAN_GS_AUTH, f"geotiff_{layername}")
    gs_util.delete_coverage_store(gs_wms_workspace, settings.LAYMAN_GS_AUTH, f"image_mosaic_{layername}")
    gs_util.delete_db_store(gs_wms_workspace, settings.LAYMAN_GS_AUTH, store_name=f"external_db_{layername}")
    gs_util.delete_security_roles(f"{gs_wms_workspace}.{layername}.r", settings.LAYMAN_GS_AUTH)
    gs_util.delete_security_roles(f"{gs_wms_workspace}.{layername}.w", settings.LAYMAN_GS_AUTH)
    # geoserver wfs
    gs_util.delete_feature_type(workspace, layername, settings.LAYMAN_GS_AUTH, store='postgresql')
    gs_util.delete_feature_type(workspace, layername, settings.LAYMAN_GS_AUTH, store=f'external_db_{layername}')
    gs_util.delete_db_store(workspace, settings.LAYMAN_GS_AUTH, store_name=f'external_db_{layername}')
    gs_util.delete_security_roles(f"{workspace}.{layername}.r", settings.LAYMAN_GS_AUTH)
    gs_util.delete_security_roles(f"{workspace}.{layername}.w", settings.LAYMAN_GS_AUTH)


def get_task_kwargs(task_fn, kwargs):
    param_names = inspect.signature(task_fn).parameters.keys()
    task_opts = {
        key: value
        for key, value in kwargs.items()
        if key in param_names
    }
    return task_opts


def run_task_sync(task_fn, args, kwargs):
    task_fn.apply(args=args, kwargs=get_task_kwargs(task_fn, kwargs), throw=True)


def get_publication_dir(publ_type, workspace, publ_name):
    publ_type_dir = f"{publ_type.split('.')[1]}s"
    publ_dir = f"{settings.LAYMAN_DATA_DIR}/workspaces/{workspace}/{publ_type_dir}/{publ_name}"
    return publ_dir


def get_layer_input_files(workspace, layername):
    input_file_dir = get_publication_dir(LAYER_TYPE, workspace, layername)
    pattern = os.path.join(input_file_dir, 'input_file', '*.*')
    filepaths = sorted(glob.glob(pattern))
    return file_util.InputFiles(saved_paths=filepaths)


def safe_delete(path, *, warn_OSError=False):
    try:
        os.rmdir(path)
    except FileNotFoundError:
        pass
    except OSError:
        if warn_OSError:
            logger.warning(f"    Directory {path} was not deleted, because it is not empty.\n{traceback.format_exc()}")
