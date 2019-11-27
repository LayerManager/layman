from functools import wraps
import importlib
import inspect
import re

from celery import chain
from flask import current_app, url_for, request

from layman import LaymanError
from layman import settings
from layman.util import USERNAME_RE, call_modules_fn, get_providers_from_source_names, get_modules_from_names, to_safe_name
from layman import celery as celery_util
from . import get_layer_sources, LAYER_TYPE

LAYERNAME_RE = USERNAME_RE

FLASK_PROVIDERS_KEY = f'{__name__}:PROVIDERS'
FLASK_SOURCES_KEY = f'{__name__}:SOURCES'


def to_safe_layer_name(value):
    return to_safe_name(value, 'layer')


def check_layername_decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        check_layername(request.view_args['layername'])
        result = f(*args, **kwargs)
        return result
    return decorated_function


def check_layername(layername):
    if not re.match(LAYERNAME_RE, layername):
        raise LaymanError(2, {'parameter': 'layername', 'expected':
            LAYERNAME_RE})


def get_sources():
    key = FLASK_SOURCES_KEY
    if key not in current_app.config:
        current_app.config[key] = get_modules_from_names(get_layer_sources())
    return current_app.config[key]


def get_providers():
    key = FLASK_PROVIDERS_KEY
    if key not in current_app.config:
        current_app.config[key] = get_providers_from_source_names(get_layer_sources())
    return current_app.config[key]


def get_layer_names(username):
    sources = get_sources()
    results = call_modules_fn(sources, 'get_layer_names', [username])
    layernames = []
    for r in results:
        layernames += r
    layernames = list(set(layernames))
    return layernames


def check_new_layername(username, layername):
    check_layername(layername)
    providers = get_providers()
    call_modules_fn(providers, 'check_new_layername', [username, layername])


def get_layer_info(username, layername):
    sources = get_sources()
    partial_infos = call_modules_fn(sources, 'get_layer_info', [username, layername])
    partial_info = {}
    for pi in partial_infos:
        partial_info.update(pi)

    last_task = _get_layer_task(username, layername)
    if last_task is None or celery_util.is_task_successful(last_task):
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
        if task_name not in TASKS_TO_LAYER_INFO_KEYS:
            continue
        for layerinfo_key in TASKS_TO_LAYER_INFO_KEYS[task_name]:
            partial_info[layerinfo_key] = source_state

    return partial_info


def get_complete_layer_info(username, layername):
    partial_info = get_layer_info(username, layername)

    if not any(partial_info):
        raise LaymanError(15, {'layername': layername})

    complete_info = {
        'name': layername,
        'url': url_for('rest_layer.get', layername=layername, username=username),
        'title': layername,
        'description': '',
        'wms': {
            'status': 'NOT_AVAILABLE'
        },
        'wfs': {
            'status': 'NOT_AVAILABLE'
        },
        'thumbnail': {
            'status': 'NOT_AVAILABLE'
        },
        'file': {
            'status': 'NOT_AVAILABLE'
        },
        'db_table': {
            'status': 'NOT_AVAILABLE'
        },
    }

    complete_info.update(partial_info)

    return complete_info


def update_layer(username, layername, layerinfo):
    sources = get_sources()
    call_modules_fn(sources, 'update_layer', [username, layername, layerinfo])


POST_TASKS = [
    'layman.layer.db.tasks.import_layer_vector_file',
    'layman.layer.geoserver.tasks.publish_layer_from_db',
    'layman.layer.geoserver.tasks.create_layer_style',
    'layman.layer.filesystem.tasks.generate_layer_thumbnail',
]


def post_layer(username, layername, task_options, use_chunk_upload):
    post_tasks = POST_TASKS.copy()
    if use_chunk_upload:
        post_tasks.insert(0, 'layman.layer.filesystem.tasks.wait_for_upload')
    post_tasks = [
        getattr(
            importlib.import_module(taskname.rsplit('.', 1)[0]),
            taskname.rsplit('.', 1)[1]
        ) for taskname in post_tasks
    ]
    post_chain = chain(*list(map(
        lambda t: _get_task_signature(username, layername, task_options, t),
        post_tasks
    )))
    # res = post_chain.apply_async()
    res = post_chain()

    celery_util.set_publication_task_info(username, LAYER_TYPE, layername, post_tasks, res)


def patch_layer(username, layername, delete_from, task_options, use_chunk_upload):
    if delete_from == 'layman.layer.filesystem.input_file':
        start_idx = 0
    elif delete_from == 'layman.layer.geoserver.sld':
        start_idx = 2
    else:
        raise Exception('Unsupported delete_from='+delete_from)

    patch_tasks = POST_TASKS[start_idx:]
    if use_chunk_upload:
        patch_tasks.insert(0, 'layman.layer.filesystem.tasks.wait_for_upload')
    patch_tasks = [
        getattr(
            importlib.import_module(taskname.rsplit('.', 1)[0]),
            taskname.rsplit('.', 1)[1]
        ) for taskname in patch_tasks
    ]

    patch_chain = chain(*list(map(
        lambda t: _get_task_signature(username, layername, task_options, t),
        patch_tasks
    )))
    # res = patch_chain.apply_async()
    res = patch_chain()

    celery_util.set_publication_task_info(username, LAYER_TYPE, layername, patch_tasks, res)


TASKS_TO_LAYER_INFO_KEYS = {
    'layman.layer.filesystem.input_file.wait_for_upload': ['file'],
    'layman.layer.db.import_layer_vector_file': ['db_table'],
    'layman.layer.geoserver.publish_layer_from_db': ['wms', 'wfs'],
    'layman.layer.geoserver.sld.create_layer_style': ['sld'],
    'layman.layer.filesystem.thumbnail.generate_layer_thumbnail': ['thumbnail'],
}


def delete_layer(username, layername, source = None):
    sources = get_sources()
    source_idx = next((
        idx for idx, m in enumerate(sources) if m.__name__ == source
    ), 0)
    end_idx = None if source_idx == 0 else source_idx-1
    sources = sources[:end_idx:-1]

    result = {}
    results = call_modules_fn(sources, 'delete_layer', [username, layername])
    for r in results:
        if r is not None:
            result.update(r)
    celery_util.delete_publication(username, LAYER_TYPE, layername)
    return result


def _get_layer_task(username, layername):
    tinfo = celery_util.get_publication_task_info(username, LAYER_TYPE, layername)
    return tinfo


def abort_layer_tasks(username, layername):
    last_task = _get_layer_task(username, layername)
    celery_util.abort_task(last_task)


def is_layer_task_ready(username, layername):
    last_task = _get_layer_task(username, layername)
    return celery_util.is_task_ready(last_task)


def _get_task_signature(username, layername, task_options, task):
    param_names = [
        pname
        for pname in inspect.signature(task).parameters.keys()
        if pname not in ['username', 'layername']
    ]
    task_opts = {
        key: value
        for key, value in task_options.items()
        if key in param_names
    }
    return task.signature(
        (username, layername),
        task_opts,
        queue=settings.LAYMAN_CELERY_QUEUE,
        immutable=True,
    )

