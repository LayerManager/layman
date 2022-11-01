import glob
import os
import pathlib
import logging
import re

from osgeo import ogr

from layman.http import LaymanError
from layman import settings, patch_mode
from layman.common import empty_method, empty_method_returns_dict
from layman.common.filesystem import util as common_util, input_file as common
from . import util, gdal as fs_gdal

LAYER_SUBDIR = __name__.split('.')[-1]
PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT
logger = logging.getLogger(__name__)

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
    filepaths = sorted(glob.glob(pattern))
    return util.InputFiles(saved_paths=filepaths)


def get_layer_info(workspace, layername):
    input_files = get_layer_input_files(workspace, layername, )

    if input_files.saved_paths:
        # input_files.raw_or_archived_main_file_path is None if user sent ZIP file by chunks without main file inside
        main_file_path = input_files.raw_or_archived_main_file_path or input_files.saved_paths[0]
        rel_main_filepath = os.path.relpath(main_file_path, common_util.get_workspace_dir(workspace))
        main_files = input_files.raw_or_archived_main_file_paths or input_files.saved_paths
        file_type = get_file_type(rel_main_filepath)
        result = {
            'file': {
                'path': rel_main_filepath,
                'paths': [os.path.relpath(filepath, common_util.get_workspace_dir(workspace)) for filepath in main_files],
                'file_type': file_type,
            },
            '_file': {
                'paths': [
                    {
                        'absolute': main_file,
                        'gdal': main_file if input_files.archive_type is None
                        else settings.COMPRESSED_FILE_EXTENSIONS[input_files.archive_type] + main_file,
                    }
                    for main_file in main_files
                ],
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


def get_all_main_file_names(filenames):
    return [fn for fn in filenames if os.path.splitext(fn)[1].lower()
            in util.get_all_allowed_main_extensions()]


def get_gdal_format_file_paths(filepath):
    compress_type = get_compressed_main_file_extension(filepath)
    result = [filepath]
    if compress_type:
        main_files = get_all_main_file_names(util.get_filenames_from_zip_storage(filepath))
        if main_files:
            result = [settings.COMPRESSED_FILE_EXTENSIONS[compress_type] + os.path.join(filepath, main_file) for main_file in main_files]
    return result


def get_file_type(main_filepath):
    if main_filepath:
        ext = os.path.splitext(main_filepath)[1].lower()
        file_type = settings.MAIN_FILE_EXTENSIONS.get(ext, settings.FILE_TYPE_UNKNOWN)
    else:
        file_type = settings.FILE_TYPE_UNKNOWN
    return file_type


def check_main_files(main_filepaths, *, check_crs=True, overview_resampling=''):
    file_type = get_file_type(main_filepaths[0])
    if file_type == settings.FILE_TYPE_VECTOR:
        if overview_resampling:
            raise LaymanError(48, f'Vector layers do not support overview resampling.')
        assert len(main_filepaths) == 1, f'main_filepaths={main_filepaths}'
        check_vector_main_file(main_filepaths[0], check_crs=check_crs)
    elif file_type == settings.FILE_TYPE_RASTER:
        check_raster_main_files(main_filepaths, check_crs=check_crs)
    else:
        raise NotImplementedError(f"Unknown file type: {file_type}")


def check_vector_main_file(main_filepath, *, check_crs=True):
    in_data_source = ogr.Open(main_filepath, 0)
    n_layers = in_data_source.GetLayerCount()
    if n_layers != 1:
        raise LaymanError(5, {'found': n_layers, 'expected': 1})
    if check_crs:
        check_vector_layer_crs(main_filepath)


def check_raster_main_files(main_filepaths, *, check_crs=True):
    for main_filepath in main_filepaths:
        fs_gdal.open_raster_file(main_filepath)
        fs_gdal.assert_valid_raster(main_filepath)
        if check_crs:
            check_raster_layer_crs(main_filepath)
    if len(main_filepaths) > 1:
        if check_crs:
            crs_list = sorted(list(set(get_raster_crs_id(main_filepath) for main_filepath in main_filepaths)))
            if len(crs_list) > 1:
                raise LaymanError(2, {'parameter': 'file',
                                      'expected': 'All main files with the same CRS.',
                                      'crs': crs_list,
                                      })
        color_interpretations_list = sorted(list(set(tuple(fs_gdal.get_color_interpretations(main_filepath)) for main_filepath in main_filepaths)))
        if len(color_interpretations_list) > 1:
            raise LaymanError(2, {'parameter': 'file',
                                  'expected': 'All main files with the same color interpretations.',
                                  'color_interpretations': color_interpretations_list,
                                  })
        bbox_list = sorted(list(set(fs_gdal.get_bbox_from_file(main_filepath) for main_filepath in main_filepaths)))
        if len(bbox_list) > 1:
            raise LaymanError(2, {'parameter': 'file',
                                  'expected': 'All main files with the same bounding box.',
                                  'bounding_boxes': bbox_list,
                                  })
        raster_size_list = sorted(list(set(tuple(fs_gdal.get_raster_size(main_filepath)) for main_filepath in main_filepaths)))
        if len(raster_size_list) > 1:
            raise LaymanError(2, {'parameter': 'file',
                                  'expected': 'All main files with the same raster size.',
                                  'raster_sizes': raster_size_list,
                                  })
        nodata_value_list = sorted(list(set(fs_gdal.get_nodata_value(main_filepath) for main_filepath in main_filepaths)))
        if len(nodata_value_list) > 1:
            raise LaymanError(2, {'parameter': 'file',
                                  'expected': 'All main files with the same nodata value.',
                                  'bounding_boxes': nodata_value_list,
                                  })
        mask_flags_list = sorted(list(set(tuple(fs_gdal.get_mask_flags(main_filepath)) for main_filepath in main_filepaths)))
        if len(mask_flags_list) > 1:
            raise LaymanError(2, {'parameter': 'file',
                                  'expected': 'All main files with the same mask flags.',
                                  'raster_sizes': mask_flags_list,
                                  })
        data_type_name_list = sorted(list(set(fs_gdal.get_data_type_name(main_filepath) for main_filepath in main_filepaths)))
        if len(data_type_name_list) > 1:
            raise LaymanError(2, {'parameter': 'file',
                                  'expected': 'All main files with the same nodata value.',
                                  'bounding_boxes': data_type_name_list,
                                  })


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


def check_filenames(workspace, layername, input_files, check_crs, ignore_existing_files=False, enable_more_main_files=False, time_regex=None):
    main_files = input_files.raw_or_archived_main_file_paths
    if len(main_files) > 1 and not enable_more_main_files:
        raise LaymanError(2, {'parameter': 'file',
                              'expected': 'At most one file with any of extensions: '
                                          + ', '.join(util.get_all_allowed_main_extensions()),
                              'files': [os.path.relpath(fp, input_files.saved_paths_dir) for fp in main_files],
                              })
    if enable_more_main_files:
        extensions = {os.path.splitext(main_filename)[1].lower() for main_filename in main_files}
        if len(extensions) > 1:
            files_list = sorted([os.path.relpath(fp, input_files.saved_paths_dir) for fp in main_files])
            extensions_list = sorted(extensions)
            raise LaymanError(2, {'parameter': 'file',
                                  'expected': 'All main files with the same extension.',
                                  'files': files_list,
                                  'extensions': extensions_list,
                                  })

    if len(input_files.raw_main_file_paths) > 0 and len(input_files.raw_paths_to_archives) > 0:
        raise LaymanError(2, {'parameter': 'file',
                              'expected': 'One compressed file or one or more uncompressed files.',
                              'files': [os.path.relpath(fp, input_files.saved_paths_dir) for fp in sorted(input_files.raw_or_archived_paths)],
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

    file_type = get_file_type(input_files.raw_or_archived_main_file_path)
    if file_type == settings.FILE_TYPE_VECTOR and time_regex is not None:
        raise LaymanError(48, f'Vector layers are not allowed to be combined with `time_regex` parameter.')

    if time_regex:
        too_long_filenames = [filename for filename in main_files if len(os.path.splitext(os.path.basename(filename))[0]) > 210]
        if len(too_long_filenames) > 0:
            raise LaymanError(48,
                              {
                                  'message': 'Too long filename in timeseries.',
                                  'expected': 'All files names shorter than 211 characters',
                                  'too_long_filenames': too_long_filenames,
                              }
                              )

        filenames = [os.path.basename(main_file) for main_file in main_files]
        unmatched_filenames = [filename for filename in filenames if not re.search(time_regex, filename)]
        if len(unmatched_filenames) > 0:
            raise LaymanError(48,
                              {
                                  'message': 'File does not match time_regex.',
                                  'expected': 'All main data files match time_regex parameter',
                                  'unmatched_filenames': unmatched_filenames,
                              }
                              )

    main_filenames = main_files
    first_main_filename = main_filenames[0]
    basename, ext = map(
        lambda s: s.lower(),
        os.path.splitext(first_main_filename)
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
                'path': os.path.relpath(first_main_filename, input_files.saved_paths_dir),
            }
            if '.prj' in missing_exts:
                detail['suggestion'] = 'Missing .prj file can be fixed also ' \
                                       'by setting "crs" parameter.'
            raise LaymanError(18, detail)
    input_file_dir = get_layer_input_file_dir(workspace, layername)
    filename_mapping, _ = get_file_name_mappings(
        input_files.raw_paths, main_filenames, layername, input_file_dir
    )

    if not ignore_existing_files:
        conflict_paths = [filename_mapping[k]
                          for k, v in filename_mapping.items()
                          if v is not None and os.path.exists(os.path.join(input_file_dir, v))]
        if len(conflict_paths) > 0:
            raise LaymanError(3, conflict_paths)


def save_layer_files(workspace, layername, input_files, check_crs, overview_resampling, *, output_dir=None, name_input_file_by_layer=True):
    if input_files.is_one_archive:
        main_filenames = input_files.raw_paths_to_archives
    else:
        main_filenames = input_files.raw_or_archived_main_file_paths
    output_dir = output_dir or ensure_layer_input_file_dir(workspace, layername)
    _, filepath_mapping = get_file_name_mappings(
        input_files.raw_paths, main_filenames, layername, output_dir, name_input_file_by_layer=name_input_file_by_layer
    )

    common.save_files(input_files.sent_streams, filepath_mapping)

    filepaths = [filepath_mapping[main_filename] for main_filename in main_filenames]
    gdal_main_filepaths = [gdal_path for filepath in filepaths for gdal_path in get_gdal_format_file_paths(filepath)]
    check_main_files(gdal_main_filepaths, check_crs=check_crs, overview_resampling=overview_resampling)


def get_unsafe_layername(input_files):
    main_filepath = input_files.raw_or_archived_main_file_path or input_files.raw_paths_to_archives[0]
    unsafe_layername = ''
    if main_filepath is not None:
        basename = os.path.basename(main_filepath)
        unsafe_layername = os.path.splitext(basename)[0]
    return unsafe_layername


def get_file_name_mappings(file_names, main_file_names, layer_name, output_dir, *, name_input_file_by_layer=True):
    main_file_names = [os.path.splitext(main_file_name)[0] for main_file_name in main_file_names]
    filename_mapping = {}
    filepath_mapping = {}
    if name_input_file_by_layer:
        for file_name in file_names:
            main_file_name = next(iter(main_file_name for main_file_name in main_file_names if file_name.startswith(main_file_name + '.')), None)
            if main_file_name:
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
