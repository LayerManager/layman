import json

import datetime
import os
import pathlib

from flask import current_app

from layman import LaymanError
from layman import settings, patch_mode
from . import util
from . import input_file

LAYER_SUBDIR = __name__.split('.')[-1]

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


def get_layer_resumable_dir(username, layername):
    resumable_dir = os.path.join(util.get_layer_dir(username, layername), LAYER_SUBDIR)
    return resumable_dir


def ensure_layer_resumable_dir(username, layername):
    resumable_dir = get_layer_resumable_dir(username, layername)
    pathlib.Path(resumable_dir).mkdir(parents=True, exist_ok=True)
    return resumable_dir


def delete_layer(username, layername):
    util.delete_layer_subdir(username, layername, LAYER_SUBDIR)
    chunk_key = get_layer_redis_total_chunks_key(username, layername)
    settings.LAYMAN_REDIS.delete(chunk_key)


get_layer_info = input_file.get_layer_info

get_publication_uuid = input_file.get_publication_uuid


def pre_publication_action_check(username, layername):
    pass


def post_layer(username, layername):
    pass


def patch_layer(username, layername):
    pass


def save_layer_files_str(username, layername, files_str, check_crs):
    filenames = files_str
    main_filename = input_file.get_main_file_name(filenames)
    input_file_dir = input_file.get_layer_input_file_dir(username, layername)
    _, filepath_mapping = input_file.get_file_name_mappings(
        filenames, main_filename, layername, input_file_dir
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
    resumable_dir = ensure_layer_resumable_dir(username, layername)
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
    return f'layman.users.{username}.layers.{layername}.total_chunks'


def save_layer_file_chunk(username, layername, parameter_name, filename, chunk,
                          chunk_number, total_chunks):
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
            settings.LAYMAN_REDIS.hset(
                get_layer_redis_total_chunks_key(username, layername),
                f'{parameter_name}:{file_info["target_file"]}',
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
                rh_key = f'{fi["layman_original_parameter"]}:{fi["target_file"]}'
                total_chunks = settings.LAYMAN_REDIS.hget(r_key, rh_key)
                # print(f'file {rh_key} {total_chunks}')
                if total_chunks is None:
                    continue
                total_chunks = int(total_chunks)
                target_fn = os.path.basename(fi['target_file'])
                chunk_paths = [
                    os.path.join(chunk_dir, _get_chunk_name(target_fn, x))
                    for x in range(1, total_chunks + 1)
                ]
                file_upload_complete = \
                    all(os.path.exists(p) for p in chunk_paths)
                if file_upload_complete:
                    current_app.logger.info(
                        'file_upload_complete ' + target_fn)
                    target_fp = fi['target_file']
                    input_file.ensure_layer_input_file_dir(username, layername)
                    with open(target_fp, "ab") as target_file:
                        for chunk_path in chunk_paths:
                            stored_chunk_file = open(chunk_path, 'rb')
                            target_file.write(stored_chunk_file.read())
                            stored_chunk_file.close()
                            os.unlink(chunk_path)
                    target_file.close()
                    settings.LAYMAN_REDIS.hdel(r_key, rh_key)
                    current_app.logger.info('Resumable file saved to: %s',
                                            target_fp)

            num_files_saved = len([
                fi for fi in files_to_upload
                if os.path.exists(fi['target_file'])
            ])
            all_files_saved = num_files_saved == len(files_to_upload)
            if all_files_saved:
                delete_layer(username, layername)
                num_chunks_saved = 0
            else:
                num_chunks_saved = len(os.listdir(chunk_dir))

            return all_files_saved, num_files_saved, num_chunks_saved
    else:
        raise LaymanError(20)


def _get_chunk_name(uploaded_filename, chunk_number):
    return uploaded_filename + "_part_%03d" % chunk_number


def get_metadata_comparison(workspace, publication_name):
    pass
