import os
from functools import partial
from layman import settings
from layman.common.filesystem import util as publ_util

LAYER_TYPE = '.'.join(__name__.split('.')[:-2])

# username
get_layers_dir = partial(publ_util.get_publications_dir, LAYER_TYPE)

# username, layername
get_layer_dir = partial(publ_util.get_publication_dir, LAYER_TYPE)

# username, layername
ensure_layer_dir = partial(publ_util.ensure_publication_dir, LAYER_TYPE)

# username, layername, subdir
delete_layer_subdir = partial(publ_util.delete_publication_subdir, LAYER_TYPE)


def get_normalized_raster_workspace_dir(workspace):
    return os.path.join(settings.LAYMAN_NORMALIZED_RASTER_DATA_DIR, 'workspaces', workspace)


def get_normalized_raster_layer_dir(workspace, layer):
    return os.path.join(get_normalized_raster_workspace_dir(workspace), 'layers', layer)


def get_normalized_raster_layer_main_filepath(workspace, layer):
    return os.path.join(get_normalized_raster_layer_dir(workspace, layer), f"{layer}.tif")


def ensure_normalized_raster_layer_dir(workspace, layer):
    gdal_dir = get_normalized_raster_layer_dir(workspace, layer)
    os.makedirs(gdal_dir, exist_ok=True)


def delete_normalized_raster_workspace(workspace):
    try:
        os.rmdir(get_normalized_raster_workspace_dir(workspace))
    except FileNotFoundError:
        pass
