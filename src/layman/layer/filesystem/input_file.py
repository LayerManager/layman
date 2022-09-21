import glob
import os
import pathlib

from osgeo import ogr

from layman.http import LaymanError
from layman import settings, patch_mode
from layman.common import empty_method, empty_method_returns_dict
from layman.common.filesystem import util as common_util, input_file as common
from . import util, gdal as fs_gdal

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
    file_ext = os.path.splitext(filepath)[1].lower()
    return file_ext if file_ext in settings.COMPRESSED_FILE_EXTENSIONS else None


def get_layer_input_files(workspace, layername):
    input_file_dir = get_layer_input_file_dir(workspace, layername)
    pattern = os.path.join(input_file_dir, '*.*')
    filepaths = glob.glob(pattern)
    return util.InputFiles(saved_paths=filepaths)


def get_layer_info(workspace, layername):
    input_files = get_layer_input_files(workspace, layername, )

    if input_files.saved_paths:
        # input_files.raw_or_archived_main_file_path is None if user sent ZIP file by chunks without main file inside
        main_file_path = input_files.raw_or_archived_main_file_path or input_files.saved_paths[0]
        rel_main_filepath = os.path.relpath(main_file_path, common_util.get_workspace_dir(workspace))
        file_type = get_file_type(rel_main_filepath)
        result = {
            'file': {
                'path': rel_main_filepath,
                'file_type': file_type,
            },
            '_file': {
                'path': main_file_path,
                'gdal_path': input_files.main_file_path_for_gdal,
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


def get_main_file_name(filenames):
    return next((fn for fn in filenames if os.path.splitext(fn)[1].lower()
                 in util.get_all_allowed_main_extensions()), None)


def get_gdal_format_file_path(filepath):
    compress_type = get_compressed_main_file_extension(filepath)
    result = filepath
    if compress_type:
        main_file = get_main_file_name(util.get_filenames_from_zip_storage(filepath))
        if main_file:
            result = settings.COMPRESSED_FILE_EXTENSIONS[compress_type] + os.path.join(filepath, main_file)
    return result


def get_file_type(main_filepath):
    if main_filepath:
        ext = os.path.splitext(main_filepath)[1].lower()
        file_type = settings.MAIN_FILE_EXTENSIONS.get(ext, settings.FILE_TYPE_UNKNOWN)
    else:
        file_type = settings.FILE_TYPE_UNKNOWN
    return file_type


def check_main_file(main_filepath, *, check_crs=True, overview_resampling=''):
    file_type = get_file_type(main_filepath)
    if file_type == settings.FILE_TYPE_VECTOR:
        if overview_resampling:
            raise LaymanError(48, f'Vector layers do not support overview resampling.')
        check_vector_main_file(main_filepath, check_crs=check_crs)
    elif file_type == settings.FILE_TYPE_RASTER:
        check_raster_main_file(main_filepath, check_crs=check_crs)
    else:
        raise NotImplementedError(f"Unknown file type: {file_type}")


def check_vector_main_file(main_filepath, *, check_crs=True):
    in_data_source = ogr.Open(main_filepath, 0)
    n_layers = in_data_source.GetLayerCount()
    if n_layers != 1:
        raise LaymanError(5, {'found': n_layers, 'expected': 1})
    if check_crs:
        check_vector_layer_crs(main_filepath)


def check_raster_main_file(main_filepath, *, check_crs=True):
    fs_gdal.open_raster_file(main_filepath)
    fs_gdal.assert_valid_raster(main_filepath)
    if check_crs:
        check_raster_layer_crs(main_filepath)


def spatial_ref_crs_to_crs_id(spatial_ref):
    crs_auth_name = spatial_ref.GetAuthorityName(None)
    crs_code = spatial_ref.GetAuthorityCode(None)
    return f"{crs_auth_name}:{crs_code}" if (crs_auth_name and crs_code) else None


def get_raster_crs(main_filepath):
    in_data_source = fs_gdal.open_raster_file(main_filepath)
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
        raise LaymanError(4, {'found': None,
                              'supported_values': settings.INPUT_SRS_LIST})
    check_spatial_ref_crs(crs)


def check_filenames(workspace, layername, input_files, check_crs, ignore_existing_files=False, enable_more_main_files=False):
    main_files = input_files.raw_or_archived_main_file_paths
    if len(main_files) > 1 and not enable_more_main_files:
        raise LaymanError(2, {'parameter': 'file',
                              'expected': 'At most one file with any of extensions: '
                                          + ', '.join(util.get_all_allowed_main_extensions()),
                              'files': [os.path.relpath(fp, input_files.saved_paths_dir) for fp in main_files],
                              })

    filenames = input_files.raw_or_archived_paths
    if not main_files:
        if len(input_files.raw_paths_to_archives) > 1:
            raise LaymanError(2, {'parameter': 'file',
                                  'expected': 'At most one file with extensions: '
                                              + ', '.join(settings.COMPRESSED_FILE_EXTENSIONS.keys()),
                                  'files': [os.path.relpath(fp, input_files.saved_paths_dir) for fp in input_files.raw_paths_to_archives],
                                  })
        if len(input_files.raw_paths_to_archives) == 0:
            raise LaymanError(2, {'parameter': 'file',
                                  'message': 'No data file in input.',
                                  'expected': 'At least one file with any of extensions: '
                                              + ', '.join(util.get_all_allowed_main_extensions())
                                              + '; or one of them in single .zip file.',
                                  'files': [os.path.relpath(fp, input_files.saved_paths_dir) for fp in filenames],
                                  })
        if input_files.is_one_archive_with_available_content:
            raise LaymanError(2, {'parameter': 'file',
                                  'message': 'Zip file without data file inside.',
                                  'expected': 'At least one file with any of extensions: '
                                              + ', '.join(util.get_all_allowed_main_extensions())
                                              + '; or one of them in single .zip file.',
                                  'files': [os.path.relpath(fp, input_files.saved_paths_dir) for fp in filenames],
                                  })
        main_files = input_files.raw_paths_to_archives
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
                'missing_extensions': missing_exts,
                'path': os.path.relpath(main_filename, input_files.saved_paths_dir),
            }
            if '.prj' in missing_exts:
                detail['suggestion'] = 'Missing .prj file can be fixed also ' \
                                       'by setting "crs" parameter.'
            raise LaymanError(18, detail)
    input_file_dir = get_layer_input_file_dir(workspace, layername)
    filename_mapping, _ = get_file_name_mappings(
        input_files.raw_paths, main_filename, layername, input_file_dir
    )

    if not ignore_existing_files:
        conflict_paths = [filename_mapping[k]
                          for k, v in filename_mapping.items()
                          if v is not None and os.path.exists(os.path.join(input_file_dir, v))]
        if len(conflict_paths) > 0:
            raise LaymanError(3, conflict_paths)


def save_layer_files(workspace, layername, input_files, check_crs, overview_resampling, *, output_dir=None, normalize_filenames=True):
    if input_files.is_one_archive:
        main_filename = input_files.raw_paths_to_archives[0]
    else:
        main_filename = input_files.raw_or_archived_main_file_path
    output_dir = output_dir or ensure_layer_input_file_dir(workspace, layername)
    _, filepath_mapping = get_file_name_mappings(
        input_files.raw_paths, main_filename, layername, output_dir, normalize_filenames=normalize_filenames
    )

    common.save_files(input_files.sent_streams, filepath_mapping)

    main_filepath = get_gdal_format_file_path(filepath_mapping[main_filename])
    check_main_file(main_filepath, check_crs=check_crs, overview_resampling=overview_resampling)


def get_unsafe_layername(input_files):
    main_filepath = input_files.raw_or_archived_main_file_path or input_files.raw_paths_to_archives[0]
    unsafe_layername = ''
    if main_filepath is not None:
        basename = os.path.basename(main_filepath)
        unsafe_layername = os.path.splitext(basename)[0]
    return unsafe_layername


def get_file_name_mappings(file_names, main_file_name, layer_name, output_dir, *, normalize_filenames=True):
    main_file_name = os.path.splitext(main_file_name)[0]
    filename_mapping = {}
    filepath_mapping = {}
    if normalize_filenames:
        for file_name in file_names:
            if file_name.startswith(main_file_name + '.'):
                new_fn = layer_name + file_name[len(main_file_name):].lower()
                filepath_mapping[file_name] = os.path.join(output_dir, new_fn)
                filename_mapping[file_name] = new_fn
            else:
                filename_mapping[file_name] = None
                filepath_mapping[file_name] = None
    else:
        filename_mapping = {file_name: file_name for file_name in file_names}
        filepath_mapping = {file_name: os.path.join(output_dir, file_name) for file_name in file_names}
    return (filename_mapping, filepath_mapping)
