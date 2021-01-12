import glob
import os
import pathlib

from osgeo import ogr

from layman.http import LaymanError
from layman import settings, patch_mode
from . import util
from layman.common.filesystem import util as common_util
from layman.common.filesystem import input_file as common
from layman.common import util as layman_util

LAYER_SUBDIR = __name__.split('.')[-1]

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


def get_layer_input_file_dir(username, layername):
    resumable_dir = os.path.join(util.get_layer_dir(username, layername),
                                 LAYER_SUBDIR)
    return resumable_dir


def ensure_layer_input_file_dir(username, layername):
    input_file_dir = get_layer_input_file_dir(username, layername)
    pathlib.Path(input_file_dir).mkdir(parents=True, exist_ok=True)
    return input_file_dir


def pre_publication_action_check(username, layername):
    pass


def post_layer(username, layername):
    pass


def patch_layer(username, layername):
    pass


def delete_layer(username, layername):
    util.delete_layer_subdir(username, layername, LAYER_SUBDIR)


def get_layer_info(username, layername):
    input_file_dir = get_layer_input_file_dir(username, layername)
    pattern = os.path.join(input_file_dir, layername + '.*')
    filenames = glob.glob(pattern)
    main_filename = get_main_file_name(filenames)
    if main_filename is not None:
        main_filename = os.path.relpath(main_filename, common_util.get_user_dir(username))
        return {
            'file': {
                'path': main_filename
            }
        }
    elif os.path.exists(util.get_layer_dir(username, layername)):
        return {
            'name': layername
        }
    else:
        return {}


from . import uuid

get_publication_uuid = uuid.get_publication_uuid


def get_layer_main_file_path(username, layername):
    input_file_dir = get_layer_input_file_dir(username, layername)
    pattern = os.path.join(input_file_dir, layername + '.*')
    filenames = glob.glob(pattern)
    return get_main_file_name(filenames)


def get_ogr_driver(main_filepath):
    ext_to_ogr_driver = {
        '.shp': "ESRI Shapefile",
        '.geojson': "GeoJSON",
    }
    ext = os.path.splitext(main_filepath)[1]
    driver_name = ext_to_ogr_driver.get(ext, None)
    return ogr.GetDriverByName(driver_name)


def check_main_file(main_filepath):
    # check feature layers in source file
    inDriver = get_ogr_driver(main_filepath)
    inDataSource = inDriver.Open(main_filepath, 0)
    n_layers = inDataSource.GetLayerCount()
    if n_layers != 1:
        raise LaymanError(5, {'found': n_layers, 'expected': 1})


def check_layer_crs(main_filepath):
    inDriver = get_ogr_driver(main_filepath)
    inDataSource = inDriver.Open(main_filepath, 0)
    feature_layer = inDataSource.GetLayerByIndex(0)

    crs = feature_layer.GetSpatialRef()
    crs_auth_name = crs.GetAuthorityName(None)
    crs_code = crs.GetAuthorityCode(None)
    crs_id = crs_auth_name + ":" + crs_code
    if crs_id not in settings.INPUT_SRS_LIST:
        raise LaymanError(4, {'found': crs_id,
                              'supported_values': settings.INPUT_SRS_LIST})


def check_filenames(username, layername, filenames, check_crs, ignore_existing_files=False):
    main_filename = get_main_file_name(filenames)
    if main_filename is None:
        raise LaymanError(2, {'parameter': 'file',
                              'expected': 'At least one file with any of extensions: '
                                          + ', '.join(settings.MAIN_FILE_EXTENSIONS)})
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
    input_file_dir = get_layer_input_file_dir(username, layername)
    filename_mapping, filepath_mapping = get_file_name_mappings(
        filenames, main_filename, layername, input_file_dir
    )

    if not ignore_existing_files:
        conflict_paths = [filename_mapping[k]
                          for k, v in filename_mapping.items()
                          if v is not None and os.path.exists(os.path.join(input_file_dir, v))]
        if len(conflict_paths) > 0:
            raise LaymanError(3, conflict_paths)


def save_layer_files(username, layername, files, check_crs):
    filenames = list(map(lambda f: f.filename, files))
    main_filename = get_main_file_name(filenames)
    input_file_dir = ensure_layer_input_file_dir(username, layername)
    filename_mapping, filepath_mapping = get_file_name_mappings(
        filenames, main_filename, layername, input_file_dir
    )

    common.save_files(files, filepath_mapping)
    # n_uploaded_files = len({k:v
    #                         for k, v in filepath_mapping.items()
    #                         if v is not None})

    check_main_file(filepath_mapping[main_filename])
    if check_crs:
        check_layer_crs(filepath_mapping[main_filename])
    # main_filename = filename_mapping[main_filename]
    target_file_paths = [
        fp for k, fp in filepath_mapping.items() if fp is not None
    ]
    return target_file_paths


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


def get_main_file_name(filenames):
    return next((fn for fn in filenames if os.path.splitext(fn)[1]
                 in settings.MAIN_FILE_EXTENSIONS), None)


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


def get_metadata_comparison(username, publication_name):
    pass
