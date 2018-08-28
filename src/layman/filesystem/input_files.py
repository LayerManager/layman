import glob
import os
from osgeo import ogr

from . import get_user_dir
from layman.settings import MAIN_FILE_EXTENSIONS, INPUT_SRS_LIST
from layman.http import LaymanError


def get_layer_info(username, layername):
    userdir = get_user_dir(username)
    pattern = os.path.join(userdir, layername+'.*')
    filenames = glob.glob(pattern)
    main_filename = get_main_file_name(filenames)
    if main_filename is not None:
        main_filename = os.path.relpath(main_filename, userdir)
        return {
            'file': {
                'path': main_filename
            }
        }
    else:
        return {}


def get_layer_names(username):
    userdir = get_user_dir(username)
    pattern = os.path.join(userdir, '*')
    filenames = glob.glob(pattern)
    main_filenames = filter(lambda fn: os.path.splitext(fn)[1]
                 in MAIN_FILE_EXTENSIONS, filenames)
    layer_names = list(map(
        lambda fn: os.path.splitext(os.path.basename(fn))[0],
        main_filenames))
    return layer_names


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


def save_files(files, filepath_mapping):
    for file in files:
        if filepath_mapping[file.filename] is None:
            continue
        # logger.info('Saving file {} as {}'.format(
        #     file.filename, filepath_mapping[file.filename]))
        file.save(filepath_mapping[file.filename])


def save_layer_files(username, layername, files):
    filenames = list(map(lambda f: f.filename, files))
    main_filename = get_main_file_name(filenames)
    if main_filename is None:
        raise LaymanError(2, {'parameter': 'file', 'expected': \
            'At least one file with any of extensions: ' + \
            ', '.join(MAIN_FILE_EXTENSIONS)})
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


def get_unsafe_layername(files):
    filenames = list(map(lambda f: f.filename, files))
    main_filename = get_main_file_name(filenames)
    unsafe_layername = ''
    if main_filename is not None:
        unsafe_layername = os.path.splitext(main_filename)[0]
    return unsafe_layername


def get_main_file_name(filenames):
    return next((fn for fn in filenames if os.path.splitext(fn)[1]
                 in MAIN_FILE_EXTENSIONS), None)


def get_file_name_mappings(file_names, main_file_name, layer_name, user_dir):
    main_file_name = os.path.splitext(main_file_name)[0]
    filename_mapping = {}
    filepath_mapping = {}
    for file_name in file_names:
        if file_name.startswith(main_file_name + '.'):
            new_fn = layer_name + file_name[len(main_file_name):]
            filepath_mapping[file_name] = os.path.join(user_dir, new_fn)
            filename_mapping[file_name] = new_fn
        else:
            filename_mapping[file_name] = None
            filepath_mapping[file_name] = None
    return (filename_mapping, filepath_mapping)