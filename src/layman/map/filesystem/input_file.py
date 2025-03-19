import json
import os
import pathlib
from urllib.parse import unquote

from layman.common import empty_method, empty_method_returns_dict
from layman.common.filesystem import input_file as common
from layman.map import MAP_TYPE
from layman.map.map_class import Map
from layman.util import url_for, get_publication_uuid
from layman import settings
from . import util

MAP_SUBDIR = __name__.rsplit('.', maxsplit=1)[-1]
pre_publication_action_check = empty_method
get_metadata_comparison = empty_method_returns_dict


def get_map_input_file_dir(publ_uuid):
    resumable_dir = os.path.join(util.get_map_dir(publ_uuid),
                                 MAP_SUBDIR)
    return resumable_dir


def ensure_map_input_file_dir(publ_uuid):
    input_file_dir = get_map_input_file_dir(publ_uuid)
    pathlib.Path(input_file_dir).mkdir(parents=True, exist_ok=True)
    return input_file_dir


def delete_map(map: Map):
    util.delete_map_subdir(map.uuid, MAP_SUBDIR)


def get_map_file(publ_uuid):
    input_file_dir = get_map_input_file_dir(publ_uuid)
    mapfile_path = os.path.join(input_file_dir, publ_uuid + '.json')
    return mapfile_path


def get_map_info(workspace, mapname, *, x_forwarded_items=None):
    publ_uuid = get_publication_uuid(workspace, MAP_TYPE, mapname)
    return get_map_info_by_uuid(publ_uuid, workspace=workspace, mapname=mapname, x_forwarded_items=x_forwarded_items) \
        if publ_uuid else {}


def get_map_info_by_uuid(publ_uuid, *, workspace, mapname, x_forwarded_items=None):
    map_file_path_absolute = get_map_file(publ_uuid)
    result = {}
    if os.path.exists(map_file_path_absolute):
        with open(map_file_path_absolute, 'r', encoding="utf-8") as map_file:
            map_json = json.load(map_file)
        map_file_path = os.path.relpath(map_file_path_absolute, settings.LAYMAN_DATA_DIR)
        result = {
            'file': {
                'path': map_file_path,
                'url': url_for('rest_workspace_map_file.get', mapname=mapname, workspace=workspace, x_forwarded_items=x_forwarded_items),
            },
            '_file': {
                'paths': {
                    'absolute': [map_file_path_absolute],
                },
                'url': url_for('rest_workspace_map_file.get', mapname=mapname, workspace=workspace, internal=True),
            },
            'title': map_json['title'] or '',
            'description': map_json['abstract'] or '',
        }
    elif os.path.exists(util.get_map_dir(publ_uuid)):
        result = {
            'name': mapname
        }
    return result


def save_map_files(publ_uuid, files):
    filenames = list(map(lambda f: f.filename, files))
    assert len(filenames) == 1
    input_file_dir = ensure_map_input_file_dir(publ_uuid)
    filepath_mapping = {
        f'{fn}': os.path.join(input_file_dir, f'{publ_uuid}.json')
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


def get_map_json(publ_uuid):
    map_file_path = get_map_file(publ_uuid)
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


# pylint: disable=unused-argument
def post_map(workspace, mapname, uuid, description, title):
    map_file_path = get_map_file(uuid)
    with open(map_file_path, 'r', encoding="utf-8") as map_file:
        map_json = json.load(map_file)
    map_json['name'] = mapname
    map_json['title'] = title
    map_json['abstract'] = description
    with open(map_file_path, 'w', encoding="utf-8") as map_file:
        json.dump(map_json, map_file, indent=4)


def patch_map(map: Map):
    post_map(map.workspace, map.name, map.uuid, map.description, map.title)
