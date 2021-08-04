import os
import shutil
import subprocess
from osgeo import gdal, gdalconst
from layman import patch_mode, settings, LaymanError
from layman.common import empty_method, empty_method_returns_dict
from . import input_file

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


def get_layer_info(workspace, layer):
    gdal_path = get_normalized_raster_layer_main_filepath(workspace, layer)
    gdal_gs_path = get_normalized_raster_layer_main_filepath(workspace, layer, geoserver=True)
    if os.path.exists(gdal_path):
        return {
            'layername': layer,
            '_file': {
                'normalized_file': {
                    'path': gdal_path,
                    'gs_path': gdal_gs_path,
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


def get_overview_counts(filepath):
    dataset = gdal.Open(filepath, gdal.GA_ReadOnly)
    result = []
    for band_id in range(1, dataset.RasterCount + 1):
        band = dataset.GetRasterBand(band_id)
        overview_count = band.GetOverviewCount()
        result.append(overview_count)
    return result


def assert_valid_raster(input_path):
    color_interp = get_color_interpretations(input_path)
    supported_color_interps = {
        ('Red', 'Green', 'Blue'),
        ('Red', 'Green', 'Blue', 'Alpha'),
        ('Gray', ),
        ('Gray', 'Alpha'),
        ('Palette', ),
    }
    if tuple(color_interp) not in supported_color_interps:
        supported_color_interps_str = ', '.join([f"[{', '.join(ci)}]" for ci in sorted(supported_color_interps)])
        raise LaymanError(2, data={
            'parameter': 'file',
            'expected': f"Any of color interpretations {supported_color_interps_str}.",
            'found': color_interp,
        })


def get_nodata_values(filepath):
    dataset = gdal.Open(filepath, gdal.GA_ReadOnly)
    result = []
    for band_id in range(1, dataset.RasterCount + 1):
        band = dataset.GetRasterBand(band_id)
        nodata_value = band.GetNoDataValue()
        result.append(nodata_value)
    return result


def get_pixel_size(filepath):
    dataset = gdal.Open(filepath, gdal.GA_ReadOnly)
    geo_transform = dataset.GetGeoTransform()
    return [geo_transform[1], geo_transform[5]]


def get_raster_size(filepath):
    dataset = gdal.Open(filepath, gdal.GA_ReadOnly)
    x_size = dataset.RasterXSize
    y_size = dataset.RasterYSize
    return [x_size, y_size]


def get_statistics(filepath):
    # If Nodata is set and it's lowest value in dataset and at least one pixel has Nodata value,
    # GetStatistics does not return Nodata value as MIN, but lowest value that is not Nodata value.
    # It's probably similar for MAX.
    dataset = gdal.Open(filepath, gdal.GA_ReadOnly)
    result = []
    for band_id in range(1, dataset.RasterCount + 1):
        band = dataset.GetRasterBand(band_id)
        stats = band.GetStatistics(False, True)  # (approx_ok, force), see
        # https://gdal.org/doxygen/classGDALRasterBand.html#a6aa58b6f0a0c17722b9bf763a96ff069
        # stats = [min, max, mean, stddev]
        result.append(stats)
    return result


def is_nodata_out_of_min_max(filepath, *, nodata_values):
    if any(val is None for val in nodata_values):
        result = False
    else:
        base_name = os.path.splitext(filepath)[0]
        vrt_file_path = base_name + '.ignore_nodata.vrt'
        vrt_options = gdal.BuildVRTOptions(hideNodata=True)
        gdal.BuildVRT(vrt_file_path, [filepath], options=vrt_options)
        stats = get_statistics(vrt_file_path)
        result = any(nodata_val < stats[band_idx][0]  # nodata_val < min
                     or nodata_val > stats[band_idx][1]  # nodata_val > max
                     for band_idx, nodata_val in enumerate(nodata_values) if nodata_val is not None)
        os.remove(vrt_file_path)
    return result


def is_normalized_alpha_needed(filepath, *, color_interp, nodata_values):
    if color_interp[-1] == 'Alpha':
        stats = get_statistics(filepath)
        alpha_min, alpha_max, _, _ = stats[-1]
        result = not alpha_min == alpha_max == 255
    elif color_interp == ['Palette']:
        result = False
    else:
        if any(val is None for val in nodata_values):
            result = False
        else:
            result = not is_nodata_out_of_min_max(filepath, nodata_values=nodata_values)
    return result


def create_vrt_file_if_needed(filepath):
    color_interp = get_color_interpretations(filepath)
    nodata_values = get_nodata_values(filepath)
    if color_interp[-1] == 'Alpha' and not is_normalized_alpha_needed(filepath, color_interp=color_interp, nodata_values=nodata_values):
        base_name = os.path.splitext(filepath)[0]
        vrt_file_path = base_name + '.vrt'
        band_list = list(range(1, len(color_interp)))
        vrt_options = gdal.BuildVRTOptions(bandList=band_list)
        gdal.BuildVRT(vrt_file_path, [filepath], options=vrt_options)
    else:
        vrt_file_path = None
    return vrt_file_path


def normalize_raster_file_async(workspace, layer, input_path, crs_id):
    color_interp = get_color_interpretations(input_path)
    result_path = get_normalized_raster_layer_main_filepath(workspace, layer)
    bash_args = [
        'gdalwarp',
        '-of', 'GTiff',
        '-co', 'PROFILE=GeoTIFF',
        '-co', 'INTERLEAVE=PIXEL',
        '-co', 'TILED=YES',
    ]
    if color_interp[:3] == ['Red', 'Green', 'Blue']:
        bash_args.extend([
            '-co', 'PHOTOMETRIC=RGB',
        ])
    # interpret NoData as transparent only if Alpha band is not available and NoData is set for each band
    src_nodata = 'None'
    nodata_values = None
    if color_interp[-1] != 'Alpha':
        nodata_values = get_nodata_values(input_path)
        if all(val is not None for val in nodata_values):
            src_nodata = ' '.join([str(val) for val in nodata_values])
    bash_args.extend([
        '-srcnodata', src_nodata,
    ])
    if color_interp != ['Palette']:
        bash_args.extend([
            '-dstnodata', 'None',
        ])
    if is_normalized_alpha_needed(input_path, color_interp=color_interp, nodata_values=nodata_values):
        bash_args.extend([
            '-dstalpha',
        ])
        if color_interp[-1] == 'Alpha':
            bash_args.extend([
                '-co', 'ALPHA=YES',
            ])
    # if output EPSG is the same as input EPSG, set pixel size (-tr) explicitly to the value of input
    input_crs_equals_output_crs = crs_id == "EPSG:3857" or \
        (crs_id is None and input_file.get_raster_crs_id(input_path) == "EPSG:3857")
    if input_crs_equals_output_crs:
        pixel_size = get_pixel_size(input_path)
        tr_list = [str(ps) for ps in pixel_size]
        tr_list.insert(0, '-tr')
        bash_args.extend(tr_list)
    if crs_id is not None:
        bash_args.extend([
            '-s_srs', f'{crs_id}',
        ])
    # resampling method
    if input_crs_equals_output_crs:
        resampling_method = 'nearest'
    elif color_interp == ['Palette']:
        resampling_method = 'mode'
    else:
        resampling_method = 'bilinear'
    bash_args.extend([
        '-r', resampling_method,
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


def add_overview_async(workspace, layer):
    normalized_path = get_normalized_raster_layer_main_filepath(workspace, layer)
    color_interp = get_color_interpretations(normalized_path)
    bash_args = [
        'gdaladdo',
    ]
    # resampling
    if color_interp == ['Palette']:
        resampling_method = 'mode'
    else:
        resampling_method = 'average'
    bash_args.extend([
        '-r', resampling_method,
    ])

    bash_args.extend([
        normalized_path,
    ])
    # print(' '.join(bash_args))
    process = subprocess.Popen(bash_args, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    return process


def get_normalized_raster_workspace_dir(workspace, *, geoserver=False):
    base_path = settings.LAYMAN_NORMALIZED_RASTER_DATA_DIR if not geoserver else settings.LAYMAN_NORMALIZED_RASTER_DATA_DIR_NAME
    return os.path.join(base_path, 'workspaces', workspace)


def get_normalized_raster_layer_dir(workspace, layer, *, geoserver=False):
    return os.path.join(get_normalized_raster_workspace_dir(workspace, geoserver=geoserver), 'layers', layer)


def get_normalized_raster_layer_main_filepath(workspace, layer, *, geoserver=False):
    return os.path.join(get_normalized_raster_layer_dir(workspace, layer, geoserver=geoserver), f"{layer}.tif")


def ensure_normalized_raster_layer_dir(workspace, layer):
    gdal_dir = get_normalized_raster_layer_dir(workspace, layer)
    os.makedirs(gdal_dir, exist_ok=True)


def delete_normalized_raster_workspace(workspace):
    try:
        os.rmdir(get_normalized_raster_workspace_dir(workspace))
    except FileNotFoundError:
        pass


def get_bbox(workspace, layer):
    filepath = get_normalized_raster_layer_main_filepath(workspace, layer)
    data = gdal.Open(filepath, gdalconst.GA_ReadOnly)
    geo_transform = data.GetGeoTransform()
    minx = geo_transform[0]
    maxy = geo_transform[3]
    maxx = minx + geo_transform[1] * data.RasterXSize
    miny = maxy + geo_transform[5] * data.RasterYSize
    result = (minx, miny, maxx, maxy)
    return result


def get_normalized_ground_sample_distance(workspace, layer):
    filepath = get_normalized_raster_layer_main_filepath(workspace, layer)
    pixel_size = get_pixel_size(filepath)
    abs_pixel_size = [abs(size) for size in pixel_size]
    distance_value = sum(abs_pixel_size) / len(abs_pixel_size)
    return distance_value
