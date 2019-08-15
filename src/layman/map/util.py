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

FLASK_PROVIDERS_KEY = f'{__name__}:PROVIDERS'
FLASK_SOURCES_KEY = f'{__name__}:SOURCES'


def to_safe_map_name(value):
    return to_safe_name(value, 'map')


def check_mapname(mapname):
    if not re.match(MAPNAME_RE, mapname):
        raise LaymanError(2, {'parameter': 'mapname', 'expected':
            MAPNAME_RE})


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


def get_map_names(username):
    sources = get_sources()
    results = call_modules_fn(sources, 'get_map_names', [username])
    mapnames = []
    for r in results:
        mapnames += r
    mapnames = list(set(mapnames))
    return mapnames


TASKS_TO_MAP_INFO_KEYS = {
    'layman.map.filesystem.thumbnail.generate_map_thumbnail': ['thumbnail'],
}


def get_map_info(username, mapname):
    sources = get_sources()
    partial_infos = call_modules_fn(sources, 'get_map_info', [username, mapname])
    partial_info = {}
    for pi in partial_infos:
        partial_info.update(pi)

    last_task = _get_map_last_task(username, mapname)
    if last_task is None or _is_task_successful(last_task):
        return partial_info

    failed = False
    for res in last_task['by_order']:
        task_name = next(k for k,v in last_task['by_name'].items() if v == res)
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
            partial_info[mapinfo_key] = source_state

    return partial_info


POST_TASKS = [
    'layman.map.filesystem.tasks.generate_map_thumbnail',
]


def post_map(username, mapname, kwargs):
    # sync processing
    sources = get_sources()
    call_modules_fn(sources, 'post_map', [username, mapname], kwargs=kwargs)

    # async processing
    post_tasks = POST_TASKS.copy()
    post_tasks = [
        getattr(
            importlib.import_module(taskname.rsplit('.', 1)[0]),
            taskname.rsplit('.', 1)[1]
        ) for taskname in post_tasks
    ]
    post_chain = chain(*list(map(
        lambda t: _get_task_signature(username, mapname, kwargs, t),
        post_tasks
    )))
    # res = post_chain.apply_async()
    res = post_chain()

    map_tasks = _get_map_tasks(username, mapname)
    tinfo = {
        'last': res,
        'by_name': {},
        'by_order': []
    }
    for post_task in reversed(post_tasks):
        tinfo['by_name'][post_task.name] = res
        tinfo['by_order'].insert(0, res)
        res = res.parent
    map_tasks.append(tinfo)


def patch_map(username, mapname, kwargs, file_changed):
    # sync processing
    sources = get_sources()
    call_modules_fn(sources, 'patch_map', [username, mapname], kwargs=kwargs)

    if not file_changed:
        return

    # async processing
    post_tasks = POST_TASKS.copy()
    post_tasks = [
        getattr(
            importlib.import_module(taskname.rsplit('.', 1)[0]),
            taskname.rsplit('.', 1)[1]
        ) for taskname in post_tasks
    ]
    post_chain = chain(*list(map(
        lambda t: _get_task_signature(username, mapname, kwargs, t),
        post_tasks
    )))
    # res = post_chain.apply_async()
    res = post_chain()

    map_tasks = _get_map_tasks(username, mapname)
    tinfo = {
        'last': res,
        'by_name': {},
        'by_order': []
    }
    for post_task in reversed(post_tasks):
        tinfo['by_name'][post_task.name] = res
        tinfo['by_order'].insert(0, res)
        res = res.parent
    map_tasks.append(tinfo)


def delete_map(username, mapname, kwargs=None):
    sources = get_sources()
    call_modules_fn(sources, 'delete_map', [username, mapname], kwargs=kwargs)


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
        'thumbnail': {
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


USER_TASKS = defaultdict(lambda: defaultdict(list))

def _is_task_successful(task_info):
    return task_info['last'].successful()


def _is_task_failed(task_info):
    return any(tr.failed() for tr in task_info['by_order'])


def _is_task_ready(task_info):
    return _is_task_successful(task_info) or _is_task_failed(task_info)


def _get_map_tasks(username, mapname):
    maptasks = USER_TASKS[username][mapname]
    return maptasks


def _get_map_last_task(username, mapname):
    maptasks = _get_map_tasks(username, mapname)
    if len(maptasks) > 0:
        return maptasks[-1]
    else:
        return None


def is_map_last_task_ready(username, mapname):
    last_task = _get_map_last_task(username, mapname)
    return last_task is None or _is_task_ready(last_task)


def abort_map_tasks(username, mapname):
    last_task = _get_map_last_task(username, mapname)
    if last_task is None or _is_task_ready(last_task):
        return

    task_results = list(filter(
        lambda r: not r.ready(),
        last_task['by_order']
    ))
    for task_result in reversed(task_results):
        task_name = next(k for k,v in last_task['by_name'].items() if v == task_result)
        # current_app.logger.info(
        #     f'processing result {task_name} {task_result.id} {task_result.state} {task_result.ready()} {task_result.successful()} {task_result.failed()}')
        if task_result.ready():
            continue
        current_app.logger.info(
            f'aborting result {task_name} {task_result.id}')
        task_result.abort()
        # task_result.revoke()
        task_result.get(propagate=False)
        current_app.logger.info('aborted ' + task_result.id)


def _get_task_signature(username, mapname, task_options, task):
    param_names = [
        pname
        for pname in inspect.signature(task).parameters.keys()
        if pname not in ['username', 'mapname']
    ]
    task_opts = {
        key: value
        for key, value in task_options.items()
        if key in param_names
    }
    return task.signature(
        (username, mapname),
        task_opts,
        queue=settings.LAYMAN_CELERY_QUEUE,
        immutable=True,
    )


