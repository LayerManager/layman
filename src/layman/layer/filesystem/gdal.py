import os
import shutil
import subprocess
from osgeo import gdal, gdalconst, osr
from layman import patch_mode, settings, LaymanError
from layman.common import empty_method, empty_method_returns_dict
from . import input_file, util

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


def get_layer_info(workspace, layer, *, extra_keys=None):
    extra_keys = extra_keys or []
    gdal_path = get_normalized_raster_layer_main_filepath(workspace, layer)
    gdal_gs_path = get_normalized_raster_layer_main_filepath(workspace, layer, geoserver=True)
    result = {}
    if os.path.exists(gdal_path):
        result = {
            'name': layer,
            '_file': {
                'normalized_file': {
                    'path': gdal_path,
                    'gs_path': gdal_gs_path,
                }
            }
        }
        file_dict = result['_file']
        input_file_gdal_path = input_file.get_layer_info(workspace, layer)['_file']['gdal_path']
        if '_file.color_interpretations' in extra_keys:
            file_dict['color_interpretations'] = get_color_interpretations(input_file_gdal_path)
        if '_file.mask_flags' in extra_keys:
            file_dict['mask_flags'] = get_mask_flags(input_file_gdal_path)
        norm_file_dict = file_dict['normalized_file']
        if '_file.normalized_file.stats' in extra_keys:
            stats = get_statistics(gdal_path)
            norm_file_dict['stats'] = stats
        if '_file.normalized_file.mask_flags' in extra_keys:
            mask_flags = get_mask_flags(gdal_path)
            norm_file_dict['mask_flags'] = mask_flags
        if '_file.normalized_file.color_interpretations' in extra_keys:
            color_interpretations = get_color_interpretations(gdal_path)
            norm_file_dict['color_interpretations'] = color_interpretations
        if '_file.normalized_file.nodata_value' in extra_keys:
            nodata_value = to_nodata_value(get_nodata_values(gdal_path))
            norm_file_dict['nodata_value'] = nodata_value
    return result


get_publication_uuid = input_file.get_publication_uuid
get_metadata_comparison = empty_method_returns_dict

pre_publication_action_check = empty_method
post_layer = empty_method
patch_layer = empty_method


def delete_layer(workspace, layername):
    try:
        shutil.rmtree(get_normalized_raster_layer_dir(workspace, layername))
    except FileNotFoundError:
        pass


def open_raster_file(filepath, mode=gdal.GA_ReadOnly):
    dataset = gdal.Open(filepath, mode)
    if not dataset:
        raise LaymanError(2, {
            'parameter': 'file',
            'message': f"Unable to open raster file.",
            'expected': f"At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.",
            'file': filepath,
        })
    return dataset


def get_color_interpretations(filepath):
    dataset = open_raster_file(filepath)
    result = []
    for band_id in range(1, dataset.RasterCount + 1):
        band = dataset.GetRasterBand(band_id)
        color_interpretation = gdal.GetColorInterpretationName(band.GetColorInterpretation())
        result.append(color_interpretation)
    return result


def get_overview_counts(filepath):
    dataset = open_raster_file(filepath)
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
    dataset = open_raster_file(filepath, gdal.GA_ReadOnly)
    result = []
    for band_id in range(1, dataset.RasterCount + 1):
        band = dataset.GetRasterBand(band_id)
        nodata_value = band.GetNoDataValue()
        result.append(nodata_value)
    return result


def to_nodata_value(nodata_values):
    first_nodata_value = nodata_values[0]
    assert all(v == first_nodata_value for v in nodata_values)
    return first_nodata_value


def get_nodata_value(filepath):
    nodata_values = get_nodata_values(filepath)
    return to_nodata_value(nodata_values)


def get_mask_flags(filepath):
    dataset = open_raster_file(filepath, gdal.GA_ReadOnly)
    all_mask_flags = [
        gdalconst.GMF_ALL_VALID,
        gdalconst.GMF_ALPHA,
        gdalconst.GMF_NODATA,
        gdalconst.GMF_PER_DATASET,
    ]
    result = []
    for band_id in range(1, dataset.RasterCount + 1):
        band = dataset.GetRasterBand(band_id)
        mask_flags_int = band.GetMaskFlags()
        mask_flag_set = set(mask_flag_int for mask_flag_int in all_mask_flags if mask_flag_int & mask_flags_int)
        result.append(mask_flag_set)
    return result


def get_pixel_size(filepath):
    dataset = open_raster_file(filepath, gdal.GA_ReadOnly)
    geo_transform = dataset.GetGeoTransform()
    return [geo_transform[1], geo_transform[5]]


def get_raster_size(filepath):
    dataset = open_raster_file(filepath, gdal.GA_ReadOnly)
    x_size = dataset.RasterXSize
    y_size = dataset.RasterYSize
    return [x_size, y_size]


def get_statistics(filepath):
    # If Nodata is set and it's lowest value in dataset and at least one pixel has Nodata value,
    # GetStatistics does not return Nodata value as MIN, but lowest value that is not Nodata value.
    # It's probably similar for MAX.
    dataset = open_raster_file(filepath, gdal.GA_ReadOnly)
    result = []
    for band_id in range(1, dataset.RasterCount + 1):
        band = dataset.GetRasterBand(band_id)
        stats = band.GetStatistics(False, True)  # (approx_ok, force), see
        # https://gdal.org/doxygen/classGDALRasterBand.html#a6aa58b6f0a0c17722b9bf763a96ff069
        # stats = [min, max, mean, stddev]
        result.append(stats)
    return result


def is_nodata_out_of_min_max(filepath, *, nodata_values):
    if to_nodata_value(nodata_values) is None:
        result = False
    else:
        base_name = os.path.splitext(util.get_deepest_real_file(filepath))[0]
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
    mask_flags = get_mask_flags(filepath)
    if color_interp[-1] == 'Alpha':
        stats = get_statistics(filepath)
        alpha_min, alpha_max, _, _ = stats[-1]
        result = not alpha_min == alpha_max == 255
    elif color_interp == ['Palette']:
        result = False
    elif mask_flags == [{gdalconst.GMF_PER_DATASET}] * 3:  # e.g. transparent JPG
        result = True
    else:
        if to_nodata_value(nodata_values) is None:
            result = False
        else:
            result = not is_nodata_out_of_min_max(filepath, nodata_values=nodata_values)
    return result


def create_vrt_file_if_needed(filepath):
    color_interp = get_color_interpretations(filepath)
    nodata_values = get_nodata_values(filepath)
    if color_interp[-1] == 'Alpha' and not is_normalized_alpha_needed(filepath, color_interp=color_interp, nodata_values=nodata_values):
        base_name = os.path.splitext(util.get_deepest_real_file(filepath))[0]
        vrt_file_path = base_name + '.vrt'
        band_list = list(range(1, len(color_interp)))
        vrt_options = gdal.BuildVRTOptions(bandList=band_list)
        gdal.BuildVRT(vrt_file_path, [filepath], options=vrt_options)
    else:
        vrt_file_path = None
    return vrt_file_path


def normalize_raster_file_async(input_path, crs_id, output_file):
    color_interp = get_color_interpretations(input_path)
    bash_args = [
        'gdalwarp',
        '-of', 'VRT',
        '-co', 'PROFILE=GeoTIFF',
        '-co', 'INTERLEAVE=PIXEL',
        '-co', 'TILED=YES',
    ]
    if color_interp[:3] == ['Red', 'Green', 'Blue']:
        bash_args.extend([
            '-co', 'PHOTOMETRIC=RGB',
        ])
    src_nodata = 'None'
    nodata_values = get_nodata_values(input_path)
    if to_nodata_value(nodata_values) is not None:
        src_nodata = ' '.join([str(val) for val in nodata_values])
    bash_args.extend([
        '-srcnodata', src_nodata,
    ])
    bash_args.extend([
        '-dstnodata', src_nodata,
    ])
    if is_normalized_alpha_needed(input_path, color_interp=color_interp, nodata_values=nodata_values):
        bash_args.extend([
            '-dstalpha',
        ])
        if color_interp[-1] == 'Alpha':
            bash_args.extend([
                '-co', 'ALPHA=YES',
            ])
    pixel_size = get_pixel_size(input_path)
    tr_list = [str(ps) for ps in pixel_size]
    tr_list.insert(0, '-tr')
    bash_args.extend(tr_list)
    if crs_id is not None:
        bash_args.extend([
            '-s_srs', f'{crs_id}',
        ])
    resampling_method = 'nearest'
    bash_args.extend([
        '-r', resampling_method,
    ])
    bash_args.extend([
        input_path,
        output_file,
    ])
    process = subprocess.Popen(bash_args, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    return process


def compress_raster_file_async(workspace, layer, *, file_to_compress):
    result_path = get_normalized_raster_layer_main_filepath(workspace, layer)
    bash_args = [
        'gdal_translate',
        '-co', 'compress=lzw',
        file_to_compress,
        result_path,
    ]
    process = subprocess.Popen(bash_args, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    return process


def add_overview_async(workspace, layer, *, overview_resampling=None):
    normalized_path = get_normalized_raster_layer_main_filepath(workspace, layer)
    color_interp = get_color_interpretations(normalized_path)
    bash_args = [
        'gdaladdo',
    ]
    # resampling
    if overview_resampling:
        resampling_method = overview_resampling
    else:
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
    data = open_raster_file(filepath, gdalconst.GA_ReadOnly)
    geo_transform = data.GetGeoTransform()
    minx = geo_transform[0]
    maxy = geo_transform[3]
    maxx = minx + geo_transform[1] * data.RasterXSize
    miny = maxy + geo_transform[5] * data.RasterYSize
    result = (minx, miny, maxx, maxy)
    return result


def get_crs(workspace, layer):
    filepath = get_normalized_raster_layer_main_filepath(workspace, layer)
    data = open_raster_file(filepath, gdalconst.GA_ReadOnly)
    spatial_reference = osr.SpatialReference(wkt=data.GetProjection())
    auth_name = spatial_reference.GetAttrValue('AUTHORITY')
    auth_srid = spatial_reference.GetAttrValue('AUTHORITY', 1)
    crs = f'{auth_name}:{auth_srid}'
    return crs


def get_normalized_ground_sample_distance_in_m(workspace, layer, *, bbox_size):
    filepath = get_normalized_raster_layer_main_filepath(workspace, layer)
    raster_size = get_raster_size(filepath)
    pixel_size = [bbox_size / raster_size[idx] for (idx, bbox_size) in enumerate(bbox_size)]
    distance_value = sum(pixel_size) / len(pixel_size)
    return distance_value
