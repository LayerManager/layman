import json
import os
import pathlib
from flask import current_app
from urllib.parse import unquote

from . import util
from layman.common.filesystem import util as common_util
from layman.common.filesystem import input_file as common
from layman.util import url_for
from layman.common import util as layman_util

MAP_SUBDIR = __name__.split('.')[-1]


def get_map_input_file_dir(username, mapname):
    resumable_dir = os.path.join(util.get_map_dir(username, mapname),
                                 MAP_SUBDIR)
    return resumable_dir


def ensure_map_input_file_dir(username, mapname):
    input_file_dir = get_map_input_file_dir(username, mapname)
    pathlib.Path(input_file_dir).mkdir(parents=True, exist_ok=True)
    return input_file_dir


def delete_map(username, mapname):
    util.delete_map_subdir(username, mapname, MAP_SUBDIR)


def get_map_file(username, mapname):
    input_file_dir = get_map_input_file_dir(username, mapname)
    mapfile_path = os.path.join(input_file_dir, mapname + '.json')
    return mapfile_path


def get_map_info(username, mapname):
    map_file_path = get_map_file(username, mapname)
    if os.path.exists(map_file_path):
        with open(map_file_path, 'r') as map_file:
            map_json = json.load(map_file)
        map_file_path = os.path.relpath(map_file_path, common_util.get_user_dir(username))
        return {
            'file': {
                'path': map_file_path,
                'url': url_for('rest_map_file.get', mapname=mapname, username=username),
            },
            'title': map_json['title'] or '',
            'description': map_json['abstract'] or '',
        }
    elif os.path.exists(util.get_map_dir(username, mapname)):
        return {
            'name': mapname
        }
    else:
        return {}


def get_map_infos(username):
    mapsdir = util.get_maps_dir(username)
    map_infos = {}
    if os.path.exists(mapsdir):
        for name in os.listdir(mapsdir):
            info = get_map_info(username, name)
            map_infos[name] = {"name": name,
                               "title": info["title"]}
    return map_infos


def get_publication_infos(username, publication_type):
    if publication_type != '.'.join(__name__.split('.')[:-2]):
        raise Exception(f'Unknown publication type {publication_type}')

    infos = get_map_infos(username)
    return infos


from . import uuid

get_publication_uuid = uuid.get_publication_uuid


def save_map_files(username, mapname, files):
    filenames = list(map(lambda f: f.filename, files))
    assert len(filenames) == 1
    input_file_dir = ensure_map_input_file_dir(username, mapname)
    filepath_mapping = {
        f'{fn}': os.path.join(input_file_dir, f'{mapname}.json')
        for fn in filenames
    }
    # print('filepath_mapping', filepath_mapping)
    common.save_files(files, filepath_mapping)

    target_file_paths = [
        fp for k, fp in filepath_mapping.items() if fp is not None
    ]
    return target_file_paths


def get_unsafe_mapname(map_json):
    unsafe_name = map_json.get('name', map_json.get('title', ''))
    return unsafe_name


def get_file_name_mappings(file_names, main_file_name, map_name, output_dir):
    main_file_name = os.path.splitext(main_file_name)[0]
    filename_mapping = {}
    filepath_mapping = {}
    for file_name in file_names:
        if file_name.startswith(main_file_name + '.'):
            new_fn = map_name + file_name[len(main_file_name):]
            filepath_mapping[file_name] = os.path.join(output_dir, new_fn)
            filename_mapping[file_name] = new_fn
        else:
            filename_mapping[file_name] = None
            filepath_mapping[file_name] = None
    return (filename_mapping, filepath_mapping)


def get_map_json(username, mapname):
    map_file_path = get_map_file(username, mapname)
    try:
        with open(map_file_path, 'r') as map_file:
            map_json = json.load(map_file)
    except FileNotFoundError:
        map_json = None
    return map_json


def unquote_urls(map_json):
    for layer_def in map_json['layers']:
        layer_url = layer_def.get('url', None)
        if layer_url is None:
            continue
        if layer_url.startswith('http%3A') or layer_url.startswith('https%3A'):
            layer_url = unquote(layer_url)
        layer_def['url'] = layer_url
    return map_json


def pre_post_publication_check(username, layername):
    pass


def post_map(username, mapname, description, title):
    map_file_path = get_map_file(username, mapname)
    with open(map_file_path, 'r') as map_file:
        map_json = json.load(map_file)
    map_json['name'] = mapname
    map_json['title'] = title
    map_json['abstract'] = description
    with open(map_file_path, 'w') as map_file:
        json.dump(map_json, map_file, indent=4)


patch_map = post_map


def get_metadata_comparison(username, publication_name):
    pass
