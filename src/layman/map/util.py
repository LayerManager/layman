from functools import wraps, partial
import importlib
import inspect
import json
from jsonschema import validate, ValidationError, Draft7Validator
import os
import re

from layman.authn.filesystem import get_authn_info
from layman.authz import get_publication_access_rights
from celery import chain
from flask import current_app, request, g

from layman import LaymanError
from layman import settings
from layman.util import USERNAME_RE, call_modules_fn, get_providers_from_source_names, get_modules_from_names, \
    to_safe_name, url_for
from layman import celery as celery_util
from . import get_map_sources, MAP_TYPE, get_map_type_def
from .filesystem import input_file
from .micka.csw import map_json_to_operates_on, map_json_to_epsg_codes
from layman.common import redis as redis_util, tasks as tasks_util, metadata as metadata_common
from layman.common import metadata as common_md

MAPNAME_RE = USERNAME_RE

FLASK_PROVIDERS_KEY = f'{__name__}:PROVIDERS'
FLASK_SOURCES_KEY = f'{__name__}:SOURCES'
FLASK_INFO_KEY = f'{__name__}:MAP_INFO'


def to_safe_map_name(value):
    return to_safe_name(value, 'map')


def check_mapname_decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        check_mapname(request.view_args['mapname'])
        result = f(*args, **kwargs)
        return result

    return decorated_function


def info_decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = request.view_args['username']
        mapname = request.view_args['mapname']
        info = get_complete_map_info(username, mapname)
        assert FLASK_INFO_KEY not in g, g.get(FLASK_INFO_KEY)
        # current_app.logger.info(f"Setting INFO of map {username}:{mapname}")
        g.setdefault(FLASK_INFO_KEY, info)
        result = f(*args, **kwargs)
        return result

    return decorated_function


def check_mapname(mapname):
    if not re.match(MAPNAME_RE, mapname):
        raise LaymanError(2, {'parameter': 'mapname',
                              'expected': MAPNAME_RE})


def get_sources():
    key = FLASK_SOURCES_KEY
    if key not in current_app.config:
        current_app.config[key] = get_modules_from_names(get_map_sources())
    return current_app.config[key]


def get_providers():
    key = FLASK_PROVIDERS_KEY
    if key not in current_app.config:
        current_app.config[key] = get_providers_from_source_names(get_map_sources())
    return current_app.config[key]


def get_map_infos(username):
    sources = get_sources()
    results = call_modules_fn(sources, 'get_map_infos', [username])
    map_infos = {}
    # TODO maybe, those two cycles can be done at once
    for source in results:
        for (name, info) in source.items():
            if map_infos.get(name) is None:
                map_infos[name] = info
            else:
                map_infos[name].update(info)
    return map_infos


TASKS_TO_MAP_INFO_KEYS = {
    'layman.map.filesystem.thumbnail.refresh': ['thumbnail'],
    'layman.map.micka.soap.refresh': ['metadata'],
}


def get_map_info(username, mapname):
    sources = get_sources()
    partial_infos = call_modules_fn(sources, 'get_map_info', [username, mapname])
    partial_info = {}
    for pi in partial_infos:
        partial_info.update(pi)

    last_task = _get_map_task(username, mapname)
    if last_task is None or celery_util.is_task_successful(last_task):
        return partial_info

    failed = False
    for res in last_task['by_order']:
        task_name = next(k for k, v in last_task['by_name'].items() if v == res)
        source_state = {
            'status': res.state if not failed else 'NOT_AVAILABLE'
        }
        if res.failed():
            failed = True
            res_exc = res.get(propagate=False)
            if isinstance(res_exc, LaymanError):
                source_state.update({
                    'error': res_exc.to_dict()
                })
        if task_name not in TASKS_TO_MAP_INFO_KEYS:
            continue
        for mapinfo_key in TASKS_TO_MAP_INFO_KEYS[task_name]:
            if mapinfo_key not in partial_info or not res.successful():
                partial_info[mapinfo_key] = source_state

    return partial_info


def post_map(username, mapname, task_options, start_at):
    # sync processing
    sources = get_sources()
    call_modules_fn(sources, 'post_map', [username, mapname], kwargs=task_options)

    # async processing
    post_tasks = tasks_util.get_task_methods(get_map_type_def(), username, mapname, task_options, start_at)
    post_chain = tasks_util.get_chain_of_methods(username, mapname, post_tasks, task_options, 'mapname')
    # res = post_chain.apply_async()
    res = post_chain()

    celery_util.set_publication_task_info(username, MAP_TYPE, mapname, post_tasks, res)


def patch_map(username, mapname, task_options, start_at):
    # sync processing
    sources = get_sources()
    call_modules_fn(sources, 'patch_map', [username, mapname], kwargs=task_options)

    # async processing
    patch_tasks = tasks_util.get_task_methods(get_map_type_def(), username, mapname, task_options, start_at)
    patch_chain = tasks_util.get_chain_of_methods(username, mapname, patch_tasks, task_options, 'mapname')
    # res = patch_chain.apply_async()
    res = patch_chain()

    celery_util.set_publication_task_info(username, MAP_TYPE, mapname, patch_tasks, res)


def delete_map(username, mapname, kwargs=None):
    sources = get_sources()
    call_modules_fn(sources[::-1], 'delete_map', [username, mapname], kwargs=kwargs)
    celery_util.delete_publication(username, MAP_TYPE, mapname)


def get_complete_map_info(username=None, mapname=None, cached=False):
    assert (username is not None and mapname is not None) or cached
    if cached:
        return g.get(FLASK_INFO_KEY)
    partial_info = get_map_info(username, mapname)

    if not any(partial_info):
        raise LaymanError(26, {'mapname': mapname})

    complete_info = {
        'name': mapname,
        'url': url_for('rest_map.get', mapname=mapname, username=username),
        'title': mapname,
        'description': '',
        'file': {
            'status': 'NOT_AVAILABLE'
        },
        'thumbnail': {
            'status': 'NOT_AVAILABLE'
        },
        'metadata': {
            'status': 'NOT_AVAILABLE'
        },
    }

    complete_info.update(partial_info)

    return complete_info


def check_file(file):
    try:
        file_json = json.load(file)
        schema_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'schema.draft-07.json'
        )
        with open(schema_path) as schema_file:
            schema_json = json.load(schema_file)
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
                    'reason': 'JSON not valid against schema layman/map/schema.draft-07.json',
                    'validation-errors': errors,
                })
            validate(instance=file_json, schema=schema_json)
            return file_json

    except ValueError:
        raise LaymanError(2, {
            'parameter': 'file',
            'reason': 'Invalid JSON syntax'
        })


def _get_map_task(username, mapname):
    tinfo = celery_util.get_publication_task_info(username, MAP_TYPE, mapname)
    return tinfo


def abort_map_tasks(username, mapname):
    last_task = _get_map_task(username, mapname)
    celery_util.abort_task(last_task)


def is_map_task_ready(username, mapname):
    last_task = _get_map_task(username, mapname)
    return last_task is None or celery_util.is_task_ready(last_task)


def get_map_owner_info(username):
    claims = get_authn_info(username).get('claims', {})
    name = claims.get('name', username)
    email = claims.get('email', '')
    result = {
        'name': name,
        'email': email,
    }
    return result


def get_groups_info(username, mapname):
    result = get_publication_access_rights(MAP_TYPE, username, mapname)
    return result


lock_decorator = redis_util.create_lock_decorator(MAP_TYPE, 'mapname', 29, is_map_task_ready)

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


def map_file_to_metadata_properties(map_json):
    result = {
        'title': map_json['title'],
        'abstract': map_json['abstract'],
        'operates_on': map_json_to_operates_on(map_json),
        'extent': [float(c) for c in map_json['extent']],
        'reference_system': map_json_to_epsg_codes(map_json),
    }
    return result


def get_metadata_comparison(username, mapname):
    layman_info = get_complete_map_info(cached=True)
    layman_props = map_info_to_metadata_properties(layman_info)
    all_props = {
        f"{layman_props['map_endpoint']}": layman_props,
    }
    map_json = get_map_file_json(username, mapname)
    if map_json:
        layman_file_props = map_file_to_metadata_properties(map_json)
        map_file_url = url_for('rest_map_file.get', mapname=mapname, username=username)
        all_props[map_file_url] = layman_file_props
    sources = get_sources()
    partial_infos = call_modules_fn(sources, 'get_metadata_comparison', [username, mapname])
    for pi in partial_infos:
        if pi is not None:
            all_props.update(pi)

    return common_md.transform_metadata_props_to_comparison(all_props)


def get_same_or_missing_prop_names(username, mapname):
    md_comparison = get_metadata_comparison(username, mapname)
    prop_names = get_syncable_prop_names()
    return common_md.get_same_or_missing_prop_names(prop_names, md_comparison)


def get_map_file_json(username, mapname):
    map_json = input_file.get_map_json(username, mapname)
    if map_json is not None:
        map_json['user'] = get_map_owner_info(username)
        map_json['groups'] = get_groups_info(username, mapname)
    return map_json
