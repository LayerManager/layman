from collections import OrderedDict, defaultdict
import importlib
import inspect
import re
import unicodedata

from flask import current_app, url_for, g
from unidecode import unidecode

from layman.http import LaymanError
from layman.settings import *
from layman import db
from layman.db import tasks
from layman import geoserver
from layman.geoserver import tasks
from layman import filesystem
from layman.filesystem import tasks
from celery import chain


USERNAME_RE = r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$"
LAYERNAME_RE = USERNAME_RE


def slugify(value):
    value = unidecode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s\-\.]', '', value).lower()
    value = re.sub(r'[\s\-\._]+', '_', value).strip('_')
    return value


def to_safe_layer_name(value):
    value = slugify(value)
    if len(value)==0:
        value = 'layer'
    elif re.match(r'^[^a-z].*', value):
        value = 'layer_'+value
    return value


def check_username(username):
    if not re.match(USERNAME_RE, username):
        raise LaymanError(2, {'parameter': 'user', 'expected': USERNAME_RE})
    providers = get_providers()
    fn_name = 'check_username'
    for m in providers:
        fn = getattr(m, fn_name, None)
        if fn is not None:
            fn(username)
        else:
            current_app.logger.warn(
                'Module {} does not have {} method.'.format(m.__name__,
                                                            fn_name))


def check_layername(layername):
    if not re.match(LAYERNAME_RE, layername):
        raise LaymanError(2, {'parameter': 'layername', 'expected':
            LAYERNAME_RE})


def check_new_layername(username, layername):
    check_layername(layername)
    providers = get_providers()
    fn_name = 'check_new_layername'
    for m in providers:
        fn = getattr(m, fn_name, None)
        if fn is not None:
            fn(username, layername)
        else:
            current_app.logger.warn(
                'Module {} does not have {} method.'.format(m.__name__,
                                                            fn_name))

def get_sources():
    key = 'layman.sources'
    if key not in current_app.config:
        active_sources = list(map(
            lambda path: importlib.import_module(path),
            SOURCES
        ))
        current_app.config[key] = active_sources
    return current_app.config[key]

def get_providers():
    key = 'layman.providers'
    if key not in current_app.config:
        paths = list(OrderedDict.fromkeys(map(
            lambda src: src[:src.rfind('.')],
            SOURCES
        )))
        providers = list(map(
            lambda path: importlib.import_module(path),
            paths
        ))
        current_app.config[key] = providers
    return current_app.config[key]

def get_layer_names(username):
    layernames = []
    active_sources = get_sources()
    fn_name = 'get_layer_names'
    for m in active_sources:
        fn = getattr(m, fn_name, None)
        if fn is not None:
            layernames += fn(username)
        else:
            current_app.logger.warn(
                'Module {} does not have {} method.'.format(m.__name__,
                                                            fn_name))
    layernames = list(set(layernames))
    return layernames

def get_layer_info(username, layername):
    partial_info = {}
    active_sources = get_sources()
    fn_name = 'get_layer_info'
    for m in active_sources:
        fn = getattr(m, fn_name, None)
        if fn is not None:
            partial_info.update(fn(username, layername))
        else:
            current_app.logger.warn(
                'Module {} does not have {} method.'.format(m.__name__,
                                                            fn_name))

    last_task = _get_layer_last_task(username, layername)
    if last_task is None or _is_task_successful(last_task):
        return partial_info

    failed = False
    for res in last_task['by_order']:
        task_name = next(k for k,v in last_task['by_name'].items() if v == res)
        if task_name not in TASKS_TO_LAYER_INFO_KEYS:
            continue
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
        for linfo_key in TASKS_TO_LAYER_INFO_KEYS[task_name]:
            partial_info[linfo_key] = source_state

    return partial_info

def get_complete_layer_info(username, layername):
    partial_info = get_layer_info(username, layername)

    if not any(partial_info):
        raise LaymanError(15, {'layername': layername})

    complete_info = {
        'name': layername,
        'url': url_for('get_layer', layername=layername, username=username),
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
    active_sources = get_sources()
    fn_name = 'update_layer'
    for m in active_sources:
        fn = getattr(m, fn_name, None)
        if fn is not None:
            fn(username, layername, layerinfo)
        else:
            current_app.logger.warn(
                'Module {} does not have {} method.'.format(m.__name__,
                                                            fn_name))


POST_TASKS = [
    db.tasks.import_layer_vector_file,
    geoserver.tasks.publish_layer_from_db,
    geoserver.tasks.create_layer_style,
    filesystem.tasks.generate_layer_thumbnail,
]


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
        queue=LAYMAN_CELERY_QUEUE,
        immutable=True,
    )


def post_layer(username, layername, task_options, use_files_str):
    post_tasks = POST_TASKS.copy()
    if use_files_str:
        post_tasks.insert(0, filesystem.tasks.wait_for_upload)
    post_chain = chain(*list(map(
        lambda t: _get_task_signature(username, layername, task_options, t),
        post_tasks
    )))
    # res = post_chain.apply_async()
    res = post_chain()

    layer_tasks = _get_layer_tasks(username, layername)
    tinfo = {
        'last': res,
        'by_name': {
            'layman.db.import_layer_vector_file': res.parent.parent.parent,
            'layman.geoserver.publish_layer_from_db': res.parent.parent,
            'layman.geoserver.sld.create_layer_style': res.parent,
            'layman.filesystem.thumbnail.generate_layer_thumbnail': res,
        },
        'by_order': [
            res,
        ]
    }
    while res.parent is not None:
        res = res.parent
        tinfo['by_order'].insert(0, res)
    if use_files_str:
        tinfo['by_name'].update({
            'layman.filesystem.input_files.wait_for_upload': res,
        })
    layer_tasks.append(tinfo)

def put_layer(username, layername, delete_from, task_options):
    if delete_from == 'layman.filesystem.input_files':
        start_idx = 0
    elif delete_from == 'layman.geoserver.sld':
        start_idx = 2
    else:
        raise Exception('Unsupported delete_from='+delete_from)

    put_tasks = POST_TASKS[start_idx:]

    post_chain = chain(*list(map(
        lambda t: _get_task_signature(username, layername, task_options, t),
        put_tasks
    )))
    # res = post_chain.apply_async()
    res = post_chain()

    tasks_by_name = {
        'layman.geoserver.sld.create_layer_style': res.parent,
        'layman.filesystem.thumbnail.generate_layer_thumbnail': res,
    }
    tasks_by_order = [
        res.parent,
        res,
    ]
    if delete_from == 'layman.filesystem.input_files':
        tasks_by_name = {
            **tasks_by_name,
            **{
                'layman.db.import_layer_vector_file': res.parent.parent.parent,
                'layman.geoserver.publish_layer_from_db': res.parent.parent,
            }
        }
        tasks_by_order = [
            res.parent.parent.parent,
            res.parent.parent,
        ] + tasks_by_order

    layer_tasks = _get_layer_tasks(username, layername)
    tinfo = {
        'last': res,
        'by_name': tasks_by_name,
        'by_order': tasks_by_order
    }
    layer_tasks.append(tinfo)

TASKS_TO_LAYER_INFO_KEYS = {
    'layman.filesystem.input_files.wait_for_upload': ['file'],
    'layman.db.import_layer_vector_file': ['db_table'],
    'layman.geoserver.publish_layer_from_db': ['wms', 'wfs'],
    'layman.filesystem.thumbnail.generate_layer_thumbnail': ['thumbnail'],
}


def delete_layer(username, layername, source = None):
    sources = get_sources()
    source_idx = next((
        idx for idx, m in enumerate(sources) if m.__name__ == source
    ), 0)
    fn_name = 'delete_layer'
    end_idx = None if source_idx == 0 else source_idx-1
    result = {}
    for m in sources[:end_idx:-1]:
        fn = getattr(m, fn_name, None)
        if fn is not None:
            partial_result = fn(username, layername)
            if partial_result is not None:
                result.update(partial_result)
        else:
            current_app.logger.warn(
                'Module {} does not have {} method.'.format(m.__name__,
                                                            fn_name))
    return result


USER_TASKS = defaultdict(lambda: defaultdict(list))


def _get_layer_tasks(username, layername):
    layertasks = USER_TASKS[username][layername]
    return layertasks


def _get_layer_last_task(username, layername):
    layertasks = _get_layer_tasks(username, layername)
    if len(layertasks) > 0:
        return layertasks[-1]
    else:
        return None


def is_layer_last_task_ready(username, layername):
    last_task = _get_layer_last_task(username, layername)
    return last_task is None or _is_task_ready(last_task)


def _is_task_successful(task_info):
    return task_info['last'].successful()


def _is_task_failed(task_info):
    return any(tr.failed() for tr in task_info['by_order'])


def _is_task_ready(task_info):
    return _is_task_successful(task_info) or _is_task_failed(task_info)


def abort_layer_tasks(username, layername):
    last_task = _get_layer_last_task(username, layername)
    if last_task is None or _is_task_ready(last_task):
        return

    task_results = list(filter(
        lambda r: not r.ready(),
        last_task['by_order']
    ))
    for task_result in reversed(task_results):
        task_name = next(k for k,v in last_task['by_name'].items() if v == task_result)
        # current_app.logger.info('processing result {} {} {} {} {} {}'
        #                         ''.format(
        #     task_name,
        #     task_result.id,
        #     task_result.state,
        #     task_result.ready(),
        #     task_result.successful(),
        #     task_result.failed(),
        # ))
        if task_result.ready():
            continue
        current_app.logger.info('aborting result {} {}'.format(
            task_name,
            task_result.id
        ))
        task_result.abort()
        # task_result.revoke()
        task_result.get(propagate=False)
        current_app.logger.info('aborted ' + task_result.id)
