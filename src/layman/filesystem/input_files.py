from collections import defaultdict
import datetime
import json
from flask import current_app
import glob
import os
from osgeo import ogr
import pathlib
import shutil

from . import get_user_dir, get_layer_dir
from layman.settings import MAIN_FILE_EXTENSIONS, INPUT_SRS_LIST, LAYMAN_REDIS
from layman.http import LaymanError


def get_layer_resumable_dir(username, layername):
    resumable_dir = os.path.join(get_layer_dir(username, layername),
                                 'input_files_resumable')
    return resumable_dir


def ensure_layer_resumable_dir(username, layername):
    resumable_dir = get_layer_resumable_dir(username, layername)
    pathlib.Path(resumable_dir).mkdir(parents=True, exist_ok=True)
    return resumable_dir


def update_layer(username, layername, layerinfo):
    pass


def delete_layer(username, layername):
    userdir = get_user_dir(username)
    pattern = os.path.join(userdir, layername + '.*')
    filenames = glob.glob(pattern)
    filenames = filter(
        lambda fn: not fn.endswith('.thumbnail.png') \
                   or not fn.endswith('.sld'),
        filenames
    )
    for filename in filenames:
        try:
            os.remove(filename)
        except OSError:
            pass
    try:
        shutil.rmtree(get_layer_dir(username, layername))
    except FileNotFoundError:
        pass
    return {}

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
    elif os.path.exists(get_layer_dir(username, layername)):
        return {
            'name': layername
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
    dirnames = list(map(
        lambda dn: os.path.basename(os.path.dirname(dn)),
        glob.glob(os.path.join(userdir, '*/'))
    ))
    layer_names += dirnames
    layer_names = list(set(layer_names))
    layer_names.sort()
    return layer_names


def get_layer_main_file_path(username, layername):
    userdir = get_user_dir(username)
    pattern = os.path.join(userdir, layername+'.*')
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


def check_filenames(username, layername, filenames, check_crs):
    main_filename = get_main_file_name(filenames)
    if main_filename is None:
        raise LaymanError(2, {'parameter': 'file', 'expected': \
            'At least one file with any of extensions: ' + \
            ', '.join(MAIN_FILE_EXTENSIONS)})
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
            lambda e: basename+e not in lower_filenames,
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


def save_layer_files(username, layername, files, check_crs):
    filenames = list(map(lambda f: f.filename, files))
    check_filenames(username, layername, filenames, check_crs)
    main_filename = get_main_file_name(filenames)
    userdir = get_user_dir(username)
    filename_mapping, filepath_mapping = get_file_name_mappings(
        filenames, main_filename, layername, userdir
    )

    save_files(files, filepath_mapping)
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


def save_layer_files_str(username, layername, files_str, check_crs):
    filenames = files_str
    check_filenames(username, layername, filenames, check_crs)
    main_filename = get_main_file_name(filenames)
    userdir = get_user_dir(username)
    _, filepath_mapping = get_file_name_mappings(
        filenames, main_filename, layername, userdir
    )
    filepath_mapping = {
        k: v for k, v in filepath_mapping.items() if v is not None
    }
    files_to_upload = [
        {
            'input_file': k,
            'target_file': v,
            'layman_original_parameter': 'file',
        } for k, v in filepath_mapping.items()
    ]

    file_content = {
        'timestamp': datetime.datetime.now().isoformat(),
        'files_to_upload': files_to_upload,
        'check_crs': check_crs,
    }
    resumable_dir = get_layer_resumable_dir(username, layername)
    ensure_layer_resumable_dir(username, layername)
    os.mkdir(os.path.join(resumable_dir, 'chunks'))
    info_path = os.path.join(resumable_dir, 'info.json')
    with open(info_path, 'w') as file:
        json.dump(file_content, file)
    return [
        {
            'file': fo['input_file'],
            'layman_original_parameter': fo['layman_original_parameter'],
        } for fo in files_to_upload
    ]


def get_layer_redis_total_chunks_key(username, layername):
    return 'layman.users.{}.layers.{}.total_chunks'.format(
                    username, layername)


def save_layer_file_chunk(username, layername, parameter_name, filename, chunk,
                          chunk_number, total_chunks):
    resumable_dir = get_layer_resumable_dir(username, layername)
    info_path = os.path.join(resumable_dir, 'info.json')
    chunk_dir = os.path.join(resumable_dir, 'chunks')
    if os.path.isfile(info_path):
        with open(info_path, 'r+') as info_file:
            info = json.load(info_file)
            files_to_upload = info['files_to_upload']
            file_info = next(
                (
                    fi for fi in files_to_upload
                    if fi['input_file'] == filename and fi[
                        'layman_original_parameter'] == parameter_name
                ),
                None
            )
            if file_info is None:
                raise LaymanError(21, {
                    'file': filename,
                    'layman_original_parameter': parameter_name,
                })
            LAYMAN_REDIS.hset(
                get_layer_redis_total_chunks_key(username, layername),
                '{}:{}'.format(parameter_name, file_info['target_file']),
                total_chunks
            )
            target_filename = os.path.basename(file_info['target_file'])
            chunk_name = _get_chunk_name(target_filename, chunk_number)
            chunk_path = os.path.join(chunk_dir, chunk_name)
            chunk.save(chunk_path)
            current_app.logger.info('Resumable chunk saved to: %s',
                                     chunk_path)

    else:
        raise LaymanError(20)


def layer_file_chunk_exists(username, layername, parameter_name, filename,
                           chunk_number):
    resumable_dir = get_layer_resumable_dir(username, layername)
    info_path = os.path.join(resumable_dir, 'info.json')
    chunk_dir = os.path.join(resumable_dir, 'chunks')
    if os.path.isfile(info_path):
        with open(info_path, 'r') as info_file:
            info = json.load(info_file)
            files_to_upload = info['files_to_upload']
            file_info = next(
                (
                    fi for fi in files_to_upload
                    if fi['input_file'] == filename and fi[
                        'layman_original_parameter'] == parameter_name
                ),
                None
            )
            if file_info is None:
                raise LaymanError(21, {
                    'file': filename,
                    'layman_original_parameter': parameter_name,
                })
            target_filepath = file_info['target_file']
            target_filename = os.path.basename(target_filepath)
            chunk_name = _get_chunk_name(target_filename, chunk_number)
            chunk_path = os.path.join(chunk_dir, chunk_name)
            return os.path.exists(chunk_path) or os.path.exists(
                target_filepath)
    else:
        raise LaymanError(20)


def layer_file_chunk_info(username, layername):
    # print('print layer_file_chunk_info')
    resumable_dir = get_layer_resumable_dir(username, layername)
    info_path = os.path.join(resumable_dir, 'info.json')
    chunk_dir = os.path.join(resumable_dir, 'chunks')
    if os.path.isfile(info_path):
        # print('print layer_file_chunk_info info_path')
        with open(info_path, 'r') as info_file:
            info = json.load(info_file)
            files_to_upload = info['files_to_upload']

            r_key = get_layer_redis_total_chunks_key(username, layername)
            for fi in files_to_upload:
                rh_key = '{}:{}'.format(
                        fi['layman_original_parameter'], fi['target_file'])
                total_chunks = LAYMAN_REDIS.hget(r_key, rh_key)
                # print('file {} {}'.format(rh_key, total_chunks))
                if total_chunks is None:
                    continue
                total_chunks = int(total_chunks)
                target_fn = os.path.basename(fi['target_file'])
                chunk_paths = [
                    os.path.join(chunk_dir, _get_chunk_name(target_fn, x))
                    for x in range(1, total_chunks + 1)
                ]
                file_upload_complete = \
                    all([os.path.exists(p) for p in chunk_paths])
                if file_upload_complete:
                    current_app.logger.info(
                        'file_upload_complete ' + target_fn)
                    target_fp = fi['target_file']
                    with open(target_fp, "ab") as target_file:
                        for chunk_path in chunk_paths:
                            stored_chunk_file = open(chunk_path, 'rb')
                            target_file.write(stored_chunk_file.read())
                            stored_chunk_file.close()
                            os.unlink(chunk_path)
                    target_file.close()
                    LAYMAN_REDIS.hdel(r_key, rh_key)
                    current_app.logger.info('Resumable file saved to: %s',
                                             target_fp)

            num_files_saved = len([
                fi for fi in files_to_upload
                if os.path.exists(fi['target_file'])
            ])
            all_files_saved = num_files_saved == len(files_to_upload)
            if all_files_saved:
                shutil.rmtree(get_layer_dir(username, layername))
                LAYMAN_REDIS.delete(r_key)
                num_chunks_saved = 0
            else:
                num_chunks_saved = len(os.listdir(chunk_dir))

            return all_files_saved, num_files_saved, num_chunks_saved
    else:
        raise LaymanError(20)


def _get_chunk_name(uploaded_filename, chunk_number):
    return uploaded_filename + "_part_%03d" % chunk_number


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