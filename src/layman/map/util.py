import importlib
import inspect
import json
from jsonschema import validate, ValidationError, Draft7Validator
import os
import re
from collections import defaultdict, OrderedDict

from celery import chain
from flask import current_app, url_for

from layman import LaymanError
from layman import settings
from layman.util import USERNAME_RE, call_modules_fn, get_providers_from_source_names, get_modules_from_names, to_safe_name
from . import get_map_sources

MAPNAME_RE = USERNAME_RE


def to_safe_map_name(value):
    return to_safe_name(value, 'map')


def check_mapname(mapname):
    if not re.match(MAPNAME_RE, mapname):
        raise LaymanError(2, {'parameter': 'mapname', 'expected':
            MAPNAME_RE})


def get_sources():
    key = 'layman.map.sources'
    if key not in current_app.config:
        current_app.config[key] = get_modules_from_names(get_map_sources())
    return current_app.config[key]


def get_providers():
    key = 'layman.map.providers'
    if key not in current_app.config:
        current_app.config[key] = get_providers_from_source_names(get_map_sources())
    return current_app.config[key]


def get_map_names(username):
    sources = get_sources()
    results = call_modules_fn(sources, 'get_map_names', [username])
    mapnames = []
    for r in results:
        mapnames += r
    mapnames = list(set(mapnames))
    return mapnames


def get_map_info(username, mapname):
    sources = get_sources()
    partial_infos = call_modules_fn(sources, 'get_map_info', [username, mapname])
    partial_info = {}
    for pi in partial_infos:
        partial_info.update(pi)

    return partial_info


def post_map(username, mapname, kwargs):
    sources = get_sources()
    call_modules_fn(sources, 'post_map', [username, mapname], kwargs=kwargs)


def get_complete_map_info(username, mapname):
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
