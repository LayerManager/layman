import os
import shutil
import subprocess
from osgeo import gdal
from layman import patch_mode, settings
from layman.common import empty_method, empty_method_returns_dict
from . import input_file

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


def get_layer_info(workspace, layer):
    gdal_path = get_normalized_raster_layer_main_filepath(workspace, layer)
    if os.path.exists(gdal_path):
        return {
            'layername': layer,
            '_file': {
                'normalized_file': {
                    'path': gdal_path,
                }
            }
        }
    return {}


get_publication_uuid = input_file.get_publication_uuid
get_metadata_comparison = empty_method_returns_dict

pre_publication_action_check = empty_method
post_layer = empty_method
patch_layer = empty_method


def delete_layer(username, layername):
    try:
        shutil.rmtree(get_normalized_raster_layer_dir(username, layername))
    except FileNotFoundError:
        pass


def get_color_interpretations(filepath):
    dataset = gdal.Open(filepath, gdal.GA_ReadOnly)
    result = []
    for band_id in range(1, dataset.RasterCount + 1):
        band = dataset.GetRasterBand(band_id)
        color_interpretation = gdal.GetColorInterpretationName(band.GetColorInterpretation())
        result.append(color_interpretation)
    return result


def normalize_raster_file_async(workspace, layer, input_path, crs_id):
    color_interp = get_color_interpretations(input_path)
    assert color_interp == ['Red', 'Green', 'Blue']
    result_path = get_normalized_raster_layer_main_filepath(workspace, layer)
    bash_args = [
        'gdalwarp',
        '-of', 'GTiff',
        '-co', 'PROFILE=GeoTIFF',
        '-co', 'PHOTOMETRIC=RGB',
        '-co', 'INTERLEAVE=PIXEL',
        '-co', 'TILED=YES',
        '-dstnodata', 'None',
        '-dstalpha',
    ]
    if crs_id is not None:
        bash_args.extend([
            '-s_srs', f'{crs_id}',
        ])
    bash_args.extend([
        '-t_srs', 'EPSG:3857',
        input_path,
        result_path,
    ])
    # print(' '.join(bash_args))
    process = subprocess.Popen(bash_args, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    return process


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
