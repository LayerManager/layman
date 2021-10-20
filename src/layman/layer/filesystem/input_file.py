import glob
import os
import pathlib

from osgeo import ogr, gdal

from layman.http import LaymanError
from layman import settings, patch_mode
from layman.common import empty_method, empty_method_returns_dict
from layman.common.filesystem import util as common_util, input_file as common
from . import util

LAYER_SUBDIR = __name__.split('.')[-1]
PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT

pre_publication_action_check = empty_method
post_layer = empty_method
patch_layer = empty_method
get_metadata_comparison = empty_method_returns_dict


def get_layer_input_file_dir(workspace, layername):
    resumable_dir = os.path.join(util.get_layer_dir(workspace, layername),
                                 LAYER_SUBDIR)
    return resumable_dir


def ensure_layer_input_file_dir(workspace, layername):
    input_file_dir = get_layer_input_file_dir(workspace, layername)
    pathlib.Path(input_file_dir).mkdir(parents=True, exist_ok=True)
    return input_file_dir


def delete_layer(workspace, layername):
    util.delete_layer_subdir(workspace, layername, LAYER_SUBDIR)


def get_compressed_main_file_extension(filepath):
    file_ext = os.path.splitext(filepath)[1]
    return file_ext if file_ext in settings.COMPRESSED_FILE_EXTENSIONS else None


def get_layer_files(workspace, layername, *, only_physical_files=False):
    input_file_dir = get_layer_input_file_dir(workspace, layername)
    pattern = os.path.join(input_file_dir, layername + '.*')
    filepaths = glob.glob(pattern)
    if len(filepaths) == 1 and not only_physical_files:
        compress_type = get_compressed_main_file_extension(filepaths[0])
        if compress_type:
            compressed_filenames = util.get_filenames_from_zip_storage(filepaths[0])
            filepaths = [os.path.join(filepaths[0], fp) for fp in compressed_filenames]
    return filepaths


def get_layer_info(workspace, layername):
    input_file_dir = get_layer_input_file_dir(workspace, layername)
    pattern = os.path.join(input_file_dir, layername + '.*')
    filepaths = glob.glob(pattern)
    abs_main_filepath = get_main_file_name(filepaths)
    if abs_main_filepath is not None:
        rel_main_filepath = os.path.relpath(abs_main_filepath, common_util.get_workspace_dir(workspace))
        file_type = get_file_type(rel_main_filepath)
        result = {
            'file': {
                'path': rel_main_filepath,
                'file_type': file_type,
            },
            '_file': {
                'path': abs_main_filepath,
            },
        }
    elif os.path.exists(util.get_layer_dir(workspace, layername)):
        result = {
            'name': layername
        }
    else:
        result = {}
    return result


from . import uuid

get_publication_uuid = uuid.get_publication_uuid


def get_all_allowed_main_extensions():
    result = list(settings.MAIN_FILE_EXTENSIONS.keys())
    return result


def get_main_file_name(filenames):
    return next((fn for fn in filenames if os.path.splitext(fn)[1]
                 in get_all_allowed_main_extensions()), None)


def get_layer_main_file_path(workspace, layername):
    input_file_dir = get_layer_input_file_dir(workspace, layername)
    pattern = os.path.join(input_file_dir, layername + '.*')
    filenames = glob.glob(pattern)
    return get_main_file_name(filenames)


def get_file_type(main_filepath):
    ext = os.path.splitext(main_filepath)[1]
    file_type = settings.MAIN_FILE_EXTENSIONS[ext]
    return file_type


def check_vector_main_file(main_filepath):
    in_data_source = ogr.Open(main_filepath, 0)
    n_layers = in_data_source.GetLayerCount()
    if n_layers != 1:
        raise LaymanError(5, {'found': n_layers, 'expected': 1})


def check_raster_main_file(main_filepath):
    in_data_source = gdal.Open(main_filepath)
    assert in_data_source is not None
    n_bands = in_data_source.RasterCount
    if n_bands not in (1, 2, 3, 4):
        raise LaymanError(5, {'found': n_bands, 'expected': 1})


def spatial_ref_crs_to_crs_id(spatial_ref):
    crs_auth_name = spatial_ref.GetAuthorityName(None)
    crs_code = spatial_ref.GetAuthorityCode(None)
    return crs_auth_name + ":" + crs_code


def get_raster_crs(main_filepath):
    in_data_source = gdal.Open(main_filepath)
    return in_data_source.GetSpatialRef()


def get_raster_crs_id(main_filepath):
    crs = get_raster_crs(main_filepath)
    return spatial_ref_crs_to_crs_id(crs)


def check_spatial_ref_crs(spatial_ref):
    crs_id = spatial_ref_crs_to_crs_id(spatial_ref)
    if crs_id not in settings.INPUT_SRS_LIST:
        raise LaymanError(4, {'found': crs_id,
                              'supported_values': settings.INPUT_SRS_LIST})


def check_vector_layer_crs(main_filepath):
    in_data_source = ogr.Open(main_filepath, 0)
    feature_layer = in_data_source.GetLayerByIndex(0)
    crs = feature_layer.GetSpatialRef()
    check_spatial_ref_crs(crs)


def check_raster_layer_crs(main_filepath):
    crs = get_raster_crs(main_filepath)
    if not crs:
        raise LaymanError(4, {'found': 'None',
                              'supported_values': settings.INPUT_SRS_LIST})
    check_spatial_ref_crs(crs)


def check_layer_crs(main_filepath):
    file_type = get_file_type(main_filepath)
    if file_type == settings.FILE_TYPE_VECTOR:
        check_vector_layer_crs(main_filepath)
    elif file_type == settings.FILE_TYPE_RASTER:
        check_raster_layer_crs(main_filepath)
    else:
        raise NotImplementedError(f"Unknown file type: {file_type}")


def check_filenames(workspace, layername, filenames, check_crs, ignore_existing_files=False):
    main_files = [fn for fn in filenames if os.path.splitext(fn)[1] in get_all_allowed_main_extensions()]
    if len(main_files) > 1:
        raise LaymanError(2, {'parameter': 'file',
                              'expected': 'At most one file with any of extensions: '
                                          + ', '.join(get_all_allowed_main_extensions()),
                              'files': main_files,
                              })

    if not main_files:
        raise LaymanError(2, {'parameter': 'file',
                              'expected': 'At least one file with any of extensions: '
                                          + ', '.join(get_all_allowed_main_extensions())})
    main_filename = main_files[0]
    basename, ext = map(
        lambda s: s.lower(),
        os.path.splitext(main_filename)
    )
    if ext == '.shp':
        lower_filenames = list(map(
            lambda fn: fn.lower(),
            filenames
        ))
        shp_exts = ['.dbf', '.shx']
        if check_crs:
            shp_exts.append('.prj')
        missing_exts = list(filter(
            lambda e: basename + e not in lower_filenames,
            shp_exts
        ))
        if len(missing_exts) > 0:
            detail = {
                'missing_extensions': missing_exts
            }
            if '.prj' in missing_exts:
                detail['suggestion'] = 'Missing .prj file can be fixed also ' \
                                       'by setting "crs" parameter.'
            raise LaymanError(18, detail)
    input_file_dir = get_layer_input_file_dir(workspace, layername)
    filename_mapping, _ = get_file_name_mappings(
        filenames, main_filename, layername, input_file_dir
    )

    if not ignore_existing_files:
        conflict_paths = [filename_mapping[k]
                          for k, v in filename_mapping.items()
                          if v is not None and os.path.exists(os.path.join(input_file_dir, v))]
        if len(conflict_paths) > 0:
            raise LaymanError(3, conflict_paths)


def save_layer_files(workspace, layername, files, check_crs, *, output_dir=None):
    filenames = list(map(lambda f: f.filename, files))
    main_filename = get_main_file_name(filenames)
    output_dir = output_dir or ensure_layer_input_file_dir(workspace, layername)
    _, filepath_mapping = get_file_name_mappings(
        filenames, main_filename, layername, output_dir
    )

    common.save_files(files, filepath_mapping)

    main_filepath = filepath_mapping[main_filename]
    file_type = get_file_type(main_filepath)
    if file_type == settings.FILE_TYPE_VECTOR:
        check_vector_main_file(main_filepath)
    elif file_type == settings.FILE_TYPE_RASTER:
        check_raster_main_file(main_filepath)
    else:
        raise NotImplementedError(f"Unknown file type: {file_type}")

    if check_crs:
        check_layer_crs(filepath_mapping[main_filename])


def get_unsafe_layername(files):
    filenames = list(map(
        lambda f: f if isinstance(f, str) else f.filename,
        files
    ))
    main_filename = get_main_file_name(filenames)
    unsafe_layername = ''
    if main_filename is not None:
        unsafe_layername = os.path.splitext(main_filename)[0]
    return unsafe_layername


def get_file_name_mappings(file_names, main_file_name, layer_name, output_dir):
    main_file_name = os.path.splitext(main_file_name)[0]
    filename_mapping = {}
    filepath_mapping = {}
    for file_name in file_names:
        if file_name.startswith(main_file_name + '.'):
            new_fn = layer_name + file_name[len(main_file_name):]
            filepath_mapping[file_name] = os.path.join(output_dir, new_fn)
            filename_mapping[file_name] = new_fn
        else:
            filename_mapping[file_name] = None
            filepath_mapping[file_name] = None
    return (filename_mapping, filepath_mapping)
