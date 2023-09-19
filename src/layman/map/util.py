from functools import wraps, partial
import json
import os
import re
import subprocess
from urllib.parse import urlparse
import requests
from jsonschema import validate, Draft7Validator
from flask import current_app, request

import layman_settings
from layman import LaymanError, util as layman_util, celery as celery_util, settings
from layman.authn.prime_db_schema import get_authn_info
from layman.common.micka import util as micka_util
from layman.common import redis as redis_util, tasks as tasks_util, metadata as metadata_common
from layman.common.util import PUBLICATION_NAME_PATTERN, PUBLICATION_MAX_LENGTH, clear_publication_info as common_clear_publication_info
from layman.layer.geoserver.util import get_gs_proxy_server_url
from layman.layer.geoserver.wms import get_layman_workspace
from layman.util import call_modules_fn, get_providers_from_source_names, get_internal_sources, \
    to_safe_name, url_for, WORKSPACE_NAME_PATTERN
from . import get_map_sources, MAP_TYPE, get_map_type_def, get_map_info_keys
from .filesystem import input_file
from .micka import csw
from .micka.csw import map_to_operates_on

MAPNAME_PATTERN = PUBLICATION_NAME_PATTERN
MAPNAME_MAX_LENGTH = PUBLICATION_MAX_LENGTH
SCHEMA_URL_PATTERN = r'^https://raw.githubusercontent.com/hslayers/map-compositions/(([0-9]{1,}.[0-9]{1,}.[0-9]{1,})|([a-zA-Z]*?))/schema.json$'
_SCHEMA_CACHE_PATH = 'tmp'
_ACCEPTED_SCHEMA_MAJOR_VERSION = '2'

FLASK_PROVIDERS_KEY = f'{__name__}:PROVIDERS'
FLASK_SOURCES_KEY = f'{__name__}:SOURCES'


def to_safe_map_name(value):
    return to_safe_name(value, 'map')


def check_mapname_decorator(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        check_mapname(request.view_args['mapname'])
        result = function(*args, **kwargs)
        return result

    return decorated_function


def check_mapname(mapname):
    if not re.match(MAPNAME_PATTERN, mapname):
        raise LaymanError(2, {'parameter': 'mapname',
                              'expected': MAPNAME_PATTERN})
    if len(mapname) > MAPNAME_MAX_LENGTH:
        raise LaymanError(2, {'parameter': 'mapname',
                              'detail': f'Map name too long ({len(mapname)}), maximum allowed length is {MAPNAME_MAX_LENGTH}.'})


def get_sources():
    key = FLASK_SOURCES_KEY
    if key not in current_app.config:
        current_app.config[key] = get_internal_sources(MAP_TYPE)
    return current_app.config[key]


def get_providers():
    key = FLASK_PROVIDERS_KEY
    if key not in current_app.config:
        current_app.config[key] = get_providers_from_source_names(get_map_sources())
    return current_app.config[key]


TASKS_TO_MAP_INFO_KEYS = {
    'layman.map.filesystem.thumbnail.refresh': ['thumbnail'],
    'layman.map.micka.soap.refresh': ['metadata'],
}


def fill_in_partial_info_statuses(info, chain_info):
    item_keys = get_map_info_keys()
    return layman_util.get_info_with_statuses(info, chain_info, TASKS_TO_MAP_INFO_KEYS, item_keys)


def get_map_info(workspace, mapname, context=None):
    partial_info = layman_util.get_publication_info(workspace, MAP_TYPE, mapname, context)

    chain_info = get_map_chain(workspace, mapname)
    filled_partial_info = fill_in_partial_info_statuses(partial_info, chain_info)
    return filled_partial_info


def pre_publication_action_check(workspace, mapname, task_options):
    # sync processing
    sources = get_sources()
    call_modules_fn(sources, 'pre_publication_action_check', [workspace, mapname], kwargs=task_options)


def post_map(workspace, mapname, task_options, start_at):
    # sync processing
    sources = get_sources()
    call_modules_fn(sources, 'post_map', [workspace, mapname], kwargs=task_options)

    # async processing
    post_tasks = tasks_util.get_task_methods(get_map_type_def(), workspace, mapname, task_options, start_at)
    post_chain = tasks_util.get_chain_of_methods(workspace, mapname, post_tasks, task_options, 'mapname')
    # res = post_chain.apply_async()
    res = post_chain()

    celery_util.set_publication_chain_info(workspace, MAP_TYPE, mapname, post_tasks, res)


def patch_map(workspace, mapname, task_options, start_at):
    # sync processing
    sources = get_sources()
    call_modules_fn(sources, 'patch_map', [workspace, mapname], kwargs=task_options)

    # async processing
    patch_tasks = tasks_util.get_task_methods(get_map_type_def(), workspace, mapname, task_options, start_at)
    patch_chain = tasks_util.get_chain_of_methods(workspace, mapname, patch_tasks, task_options, 'mapname')
    # res = patch_chain.apply_async()
    res = patch_chain()

    celery_util.set_publication_chain_info(workspace, MAP_TYPE, mapname, patch_tasks, res)


def delete_map(workspace, mapname, kwargs=None):
    sources = get_sources()
    call_modules_fn(sources[::-1], 'delete_map', [workspace, mapname], kwargs=kwargs)
    celery_util.delete_publication(workspace, MAP_TYPE, mapname)


def clear_publication_info(layer_info):
    clear_info = common_clear_publication_info(layer_info)
    clear_info.pop('image_mosaic')
    return clear_info


def get_complete_map_info(workspace, mapname, *, x_forwarded_prefix=None):
    partial_info = get_map_info(workspace, mapname, context={'x_forwarded_prefix': x_forwarded_prefix})

    if not any(partial_info):
        raise LaymanError(26, {'mapname': mapname})

    item_keys = ['file', 'thumbnail', 'metadata', ]

    complete_info = {
        'name': mapname,
        'url': url_for('rest_workspace_map.get', mapname=mapname, workspace=workspace, x_forwarded_prefix=x_forwarded_prefix),
        'title': mapname,
        'description': '',
    }

    for key in item_keys:
        complete_info[key] = {'status': 'NOT_AVAILABLE'}

    complete_info.update(partial_info)

    complete_info['layman_metadata'] = {'publication_status': layman_util.get_publication_status(workspace, MAP_TYPE, mapname,
                                                                                                 complete_info, item_keys)}

    complete_info = clear_publication_info(complete_info)

    return complete_info


def get_composition_schema(url):
    match = re.compile(SCHEMA_URL_PATTERN).match(url)
    if not match:
        raise LaymanError(2, {
            'parameter': 'file',
            'reason': 'Invalid schema url',
            'regular_expression': SCHEMA_URL_PATTERN,
        })
    version = url.split('/')[-2]
    if version.split('.')[0] != _ACCEPTED_SCHEMA_MAJOR_VERSION:
        raise LaymanError(2, {
            'parameter': 'file',
            'reason': 'Invalid schema version',
            'expected': _ACCEPTED_SCHEMA_MAJOR_VERSION + '.x.x',
        })

    schema_file_name = os.path.join(*url.split('/')[-1:])
    schema_path = os.path.join(*url.split('/')[-3:-1])
    local_path = os.path.join(_SCHEMA_CACHE_PATH, schema_path)
    local_full_path = os.path.join(local_path, schema_file_name)
    if os.path.exists(local_full_path):
        with open(local_full_path, encoding="utf-8") as schema_file:
            schema_json = json.load(schema_file)
    else:
        res = requests.get(url,
                           timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
        res.raise_for_status()
        schema_txt = res.text
        schema_json = json.loads(schema_txt)

        os.makedirs(local_path, exist_ok=True)
        with open(local_full_path, "w", encoding="utf-8") as out_file:
            json.dump(schema_json, out_file, indent=4)
    return schema_json


def check_file(file):
    try:
        file_json = json.load(file)
    except ValueError as exc:
        raise LaymanError(2, {
            'parameter': 'file',
            'reason': 'Invalid JSON syntax'
        }) from exc

    try:
        schema_url = file_json['describedBy']
    except KeyError as exc:
        raise LaymanError(2, {
            'parameter': 'file',
            'reason': 'Missing key `describedBy`',
            'expected': 'JSON file according schema `https://github.com/hslayers/map-compositions`, version ' + _ACCEPTED_SCHEMA_MAJOR_VERSION,
        }) from exc

    schema_json = get_composition_schema(schema_url)

    validator = Draft7Validator(schema_json)
    if not validator.is_valid(file_json):
        errors = [
            {
                'message': e.message,
                'absolute_path': list(e.absolute_path),
            }
            for e in validator.iter_errors(file_json)
        ]
        raise LaymanError(2, {
            'parameter': 'file',
            'reason': f'JSON not valid against schema {schema_url}',
            'validation-errors': errors,
        })
    validate(instance=file_json, schema=schema_json)

    map_crs = get_crs_from_json(file_json)
    if map_crs not in settings.INPUT_SRS_LIST:
        raise LaymanError(4, {'found': map_crs,
                              'supported_values': settings.INPUT_SRS_LIST})

    return file_json


def get_map_chain(workspace, mapname):
    chain_info = celery_util.get_publication_chain_info(workspace, MAP_TYPE, mapname)
    return chain_info


def abort_map_chain(workspace, mapname):
    celery_util.abort_publication_chain(workspace, MAP_TYPE, mapname)


def is_map_chain_ready(workspace, mapname):
    chain_info = get_map_chain(workspace, mapname)
    return chain_info is None or celery_util.is_chain_ready(chain_info)


def get_map_owner_info(username):
    claims = get_authn_info(username).get('claims', {})
    name = claims.get('name', username)
    email = claims.get('email', '')
    result = {
        'name': name,
        'email': email,
    }
    return result


lock_decorator = redis_util.create_lock_decorator(MAP_TYPE, 'mapname', is_map_chain_ready)

get_syncable_prop_names = partial(metadata_common.get_syncable_prop_names, MAP_TYPE)


def map_info_to_metadata_properties(info):
    result = {
        'title': info['title'],
        'identifier': {
            'identifier': info['url'],
            'label': info['name'],
        },
        'abstract': info['description'],
        'graphic_url': info.get('thumbnail', {}).get('url', None),
        'map_endpoint': info['url'],
        'map_file_endpoint': info.get('file', {}).get('url', None),
    }
    return result


def get_bbox_from_json(map_json):
    return float(map_json['extent'][0]), float(map_json['extent'][1]), float(map_json['extent'][2]), float(map_json['extent'][3])


def get_native_bbox_from_json(map_json):
    return tuple(map_json['nativeExtent'][0:4])


def get_crs_from_json(map_json):
    return map_json['projection'].upper()


def map_file_to_metadata_properties(workspace, mapname, map_json, operates_on_muuids_filter):
    result = {
        'title': map_json['title'],
        'abstract': map_json['abstract'],
        'operates_on': map_to_operates_on(workspace, mapname, operates_on_muuids_filter=operates_on_muuids_filter),
        'extent': list(get_bbox_from_json(map_json)),
        'reference_system': [get_crs_from_json(map_json)],
    }
    return result


def get_metadata_comparison(workspace, mapname):
    layman_info = get_complete_map_info(workspace, mapname)
    layman_props = map_info_to_metadata_properties(layman_info)
    all_props = {
        f"{layman_props['map_endpoint']}": layman_props,
    }
    sources = get_sources()
    partial_infos = call_modules_fn(sources, 'get_metadata_comparison', [workspace, mapname])
    for partial_info in partial_infos.values():
        if partial_info is not None:
            all_props.update(partial_info)
    map_json = get_map_file_json(workspace, mapname)
    if map_json:
        soap_operates_on = next(iter(partial_infos[csw].values()))['operates_on'] if partial_infos[csw] else []
        operates_on_muuids_filter = micka_util.operates_on_values_to_muuids(soap_operates_on)
        layman_file_props = map_file_to_metadata_properties(workspace, mapname, map_json, operates_on_muuids_filter)
        map_file_url = url_for('rest_workspace_map_file.get', mapname=mapname, workspace=workspace)
        all_props[map_file_url] = layman_file_props

    return metadata_common.transform_metadata_props_to_comparison(all_props)


def get_same_or_missing_prop_names(workspace, mapname):
    md_comparison = get_metadata_comparison(workspace, mapname)
    prop_names = get_syncable_prop_names()
    return metadata_common.get_same_or_missing_prop_names(prop_names, md_comparison)


def _adjust_url(*, url_obj, url_key, proxy_prefix):
    url_str = url_obj.get(url_key, '')
    if not url_str:
        return
    gs_path_pattern = r'^' + layman_util.CLIENT_PROXY_ONLY_PATTERN + \
                      re.escape(layman_settings.LAYMAN_GS_PATH) + r'(?P<path_postfix>.*)$'
    parsed_url = urlparse(url_str)
    match = re.match(gs_path_pattern, parsed_url.path)
    if match:
        # replace scheme and netloc, because LAYMAN_PUBLIC_URL_SCHEME or LAYMAN_PROXY_SERVER_NAME may have changed
        new_url = parsed_url._replace(
            scheme=settings.LAYMAN_PUBLIC_URL_SCHEME,
            netloc=settings.LAYMAN_PROXY_SERVER_NAME,
            path=proxy_prefix + layman_settings.LAYMAN_GS_PATH + match.group('path_postfix'),
        )
        url_obj[url_key] = new_url.geturl()


def get_map_file_json(workspace, mapname, *, adjust_urls=True, x_forwarded_prefix=None):
    x_forwarded_prefix = x_forwarded_prefix or ''
    map_json = input_file.get_map_json(workspace, mapname)

    if adjust_urls:
        input_file.unquote_urls(map_json)
        map_layers = layman_util.get_publication_info(workspace, MAP_TYPE, mapname, context={'keys': ['map_layers']})['_map_layers']
        ml_indices = {ml['index'] for ml in map_layers}

        for ml_idx in ml_indices:
            map_layer = map_json['layers'][ml_idx]
            _adjust_url(url_obj=map_layer, url_key='url', proxy_prefix=x_forwarded_prefix)
            _adjust_url(url_obj=map_layer.get('protocol', {}), url_key='url', proxy_prefix=x_forwarded_prefix)

    if map_json is not None:
        map_json['user'] = get_map_owner_info(workspace)
        map_json.pop("groups", None)
    return map_json


def find_maps_by_grep(regexp):
    data_dir = settings.LAYMAN_DATA_DIR
    grep_cmd = f"grep -r -E '{regexp}' {data_dir} || [ $? = 1 ]"
    grep_process = subprocess.check_output(grep_cmd, shell=True,).decode('ascii')
    map_paths = [line.split(':')[0] for line in grep_process.split('\n')
                 if line.split(':')[0]]

    maps = {(map_path.split('/')[-5], map_path.split('/')[-3]) for map_path in map_paths}
    return maps


def _get_layer_url_from_wms_json(map_layer):
    return map_layer.get('url')


def _get_layer_names_from_wms_json(map_layer):
    return [
        n for n in map_layer.get('params', {}).get('LAYERS', '').split(',')
        if len(n) > 0
    ]


def _get_layer_url_from_vector_json(map_layer):
    protocol = map_layer.get('protocol', {})
    return protocol.get('url') if protocol.get('format', '').split('.')[-1] == 'WFS' else None


def _get_layer_names_from_vector_json(map_layer):
    return [
        n for n in map_layer.get('name', '').split(',')
        if len(n) > 0
    ]


def get_layers_from_json(map_json):
    map_json = input_file.unquote_urls(map_json)
    gs_server_url = get_gs_proxy_server_url()
    gs_url_pattern = r'^' + re.escape(gs_server_url) + layman_util.CLIENT_PROXY_ONLY_PATTERN + \
                     re.escape(layman_settings.LAYMAN_GS_PATH) + \
                     r'(?:(?P<workspace>' + layman_util.WORKSPACE_NAME_ONLY_PATTERN + r')/)?' \
                     + r'(?:ows|wms|wfs).*$'
    found_layers = []
    for layer_idx, map_layer in enumerate(map_json['layers']):
        class_name = map_layer.get('className', '').split('.')[-1]
        layer_url_getter = {
            'WMS': _get_layer_url_from_wms_json,
            'Vector': _get_layer_url_from_vector_json,
        }.get(class_name)
        layer_url = layer_url_getter(map_layer)
        if not layer_url:
            continue
        match = re.match(gs_url_pattern, layer_url)
        if not match:
            continue
        url_geoserver_workspace = match.group('workspace')
        layer_names_getter = {
            'WMS': _get_layer_names_from_wms_json,
            'Vector': _get_layer_names_from_vector_json,
        }.get(class_name)
        layer_names = layer_names_getter(map_layer)
        for full_layername in layer_names:
            if not url_geoserver_workspace:
                layername_parts = full_layername.split(':')
                if len(layername_parts) != 2:
                    continue
                layer_geoserver_workspace, layername = layername_parts
                match = re.match(WORKSPACE_NAME_PATTERN, layer_geoserver_workspace)
                if not match:
                    continue
            else:
                layer_geoserver_workspace = url_geoserver_workspace
                layername = full_layername
            match = re.match(PUBLICATION_NAME_PATTERN, layername)
            if not match:
                continue
            layer_workspace = get_layman_workspace(layer_geoserver_workspace)
            layer_def = (layer_workspace, layername, layer_idx)
            if layer_def not in found_layers:
                found_layers.append(layer_def)
    return found_layers
