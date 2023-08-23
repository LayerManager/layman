import json
import os
import pathlib
from urllib.parse import unquote

from layman.common import empty_method, empty_method_returns_dict
from layman.common.filesystem import util as common_util
from layman.common.filesystem import input_file as common
from layman.util import url_for
from . import util

MAP_SUBDIR = __name__.rsplit('.', maxsplit=1)[-1]
pre_publication_action_check = empty_method
get_metadata_comparison = empty_method_returns_dict


def get_map_input_file_dir(workspace, mapname):
    resumable_dir = os.path.join(util.get_map_dir(workspace, mapname),
                                 MAP_SUBDIR)
    return resumable_dir


def ensure_map_input_file_dir(workspace, mapname):
    input_file_dir = get_map_input_file_dir(workspace, mapname)
    pathlib.Path(input_file_dir).mkdir(parents=True, exist_ok=True)
    return input_file_dir


def delete_map(workspace, mapname):
    util.delete_map_subdir(workspace, mapname, MAP_SUBDIR)


def get_map_file(workspace, mapname):
    input_file_dir = get_map_input_file_dir(workspace, mapname)
    mapfile_path = os.path.join(input_file_dir, mapname + '.json')
    return mapfile_path


def get_map_info(workspace, mapname, *, x_forwarded_prefix=None):
    map_file_path = get_map_file(workspace, mapname)
    result = {}
    if os.path.exists(map_file_path):
        with open(map_file_path, 'r', encoding="utf-8") as map_file:
            map_json = json.load(map_file)
        map_file_path = os.path.relpath(map_file_path, common_util.get_workspace_dir(workspace))
        result = {
            'file': {
                'path': map_file_path,
                'url': url_for('rest_workspace_map_file.get', mapname=mapname, workspace=workspace, x_forwarded_prefix=x_forwarded_prefix),
            },
            '_file': {
                'url': url_for('rest_workspace_map_file.get', mapname=mapname, workspace=workspace, internal=True),
            },
            'title': map_json['title'] or '',
            'description': map_json['abstract'] or '',
        }
    elif os.path.exists(util.get_map_dir(workspace, mapname)):
        result = {
            'name': mapname
        }
    return result


from . import uuid

get_publication_uuid = uuid.get_publication_uuid


def save_map_files(workspace, mapname, files):
    filenames = list(map(lambda f: f.filename, files))
    assert len(filenames) == 1
    input_file_dir = ensure_map_input_file_dir(workspace, mapname)
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


def get_map_json(workspace, mapname):
    map_file_path = get_map_file(workspace, mapname)
    try:
        with open(map_file_path, 'r', encoding="utf-8") as map_file:
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


def post_map(workspace, mapname, description, title):
    map_file_path = get_map_file(workspace, mapname)
    with open(map_file_path, 'r', encoding="utf-8") as map_file:
        map_json = json.load(map_file)
    map_json['name'] = mapname
    map_json['title'] = title
    map_json['abstract'] = description
    with open(map_file_path, 'w', encoding="utf-8") as map_file:
        json.dump(map_json, map_file, indent=4)


patch_map = post_map
