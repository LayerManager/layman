import os
from osgeo import ogr
import pathlib

from .http import LaymanError
from .settings import *
from .util import get_main_file_name, to_safe_layer_name, get_file_name_mappings


def get_user_dir(username):
    userdir = os.path.join(LAYMAN_DATA_PATH, username)
    return userdir


def ensure_user_dir(username):
    userdir = get_user_dir(username)
    pathlib.Path(userdir).mkdir(exist_ok=True)
    return userdir


def save_files(files, filepath_mapping):
    for file in files:
        if filepath_mapping[file.filename] is None:
            continue
        # logger.info('Saving file {} as {}'.format(
        #     file.filename, filepath_mapping[file.filename]))
        file.save(filepath_mapping[file.filename])


def check_main_file(main_filepath):
    # check feature layers in source file
    inDriver = ogr.GetDriverByName("GeoJSON")
    inDataSource = inDriver.Open(main_filepath, 0)
    n_layers = inDataSource.GetLayerCount()
    if n_layers != 1:
        raise LaymanError(5, {'found': n_layers, 'expected': 1})


def check_layer_crs(main_filepath):
    inDriver = ogr.GetDriverByName("GeoJSON")
    inDataSource = inDriver.Open(main_filepath, 0)
    feature_layer = inDataSource.GetLayerByIndex(0)

    crs = feature_layer.GetSpatialRef()
    crs_auth_name = crs.GetAuthorityName(None)
    crs_code = crs.GetAuthorityCode(None)
    crs_id = crs_auth_name+":"+crs_code
    if crs_id not in INPUT_SRS_LIST:
        raise LaymanError(4, {'found': crs_id,
                              'supported_values': INPUT_SRS_LIST})


def get_main_filename(files):
    filenames = list(map(lambda f: f.filename, files))
    main_filename = get_main_file_name(filenames)
    return main_filename


def get_safe_layername(unsafe_layername, files):
    main_filename = get_main_filename(files)
    if unsafe_layername is None:
        unsafe_layername = ''
    if len(unsafe_layername) == 0 and main_filename is not None:
        unsafe_layername = os.path.splitext(main_filename)[0]
    layername = to_safe_layer_name(unsafe_layername)
    return layername


def save_layer_files(username, layername, files):
    main_filename = get_main_filename(files)
    if main_filename is None:
        raise LaymanError(2, {'parameter': 'file', 'expected': \
            'At least one file with any of extensions: ' + \
            ', '.join(MAIN_FILE_EXTENSIONS)})
    filenames = list(map(lambda f: f.filename, files))
    userdir = get_user_dir(username)
    filename_mapping, filepath_mapping = get_file_name_mappings(
        filenames, main_filename, layername, userdir
    )

    conflict_paths = [filename_mapping[k]
                      for k, v in filename_mapping.items()
                      if v is not None and os.path.isfile(os.path.join(
            userdir, v))]
    if len(conflict_paths) > 0:
        raise LaymanError(3, conflict_paths)

    save_files(files, filepath_mapping)
    # n_uploaded_files = len({k:v
    #                         for k, v in filepath_mapping.items()
    #                         if v is not None})

    check_main_file(filepath_mapping[main_filename])
    main_filename = filename_mapping[main_filename]
    return main_filename
