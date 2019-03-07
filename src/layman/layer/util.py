import inspect
import re
import unicodedata
from collections import defaultdict

from celery import chain
from flask import current_app, url_for
from unidecode import unidecode

from layman.layer import db, geoserver, filesystem
from layman.layer.db import tasks
from layman.layer.geoserver import tasks
from layman.layer.filesystem import tasks
from layman import LaymanError, LAYMAN_CELERY_QUEUE
from layman.util import USERNAME_RE, get_sources, get_providers

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


def check_layername(layername):
    if not re.match(LAYERNAME_RE, layername):
        raise LaymanError(2, {'parameter': 'layername', 'expected':
            LAYERNAME_RE})


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
                f'Module {m.__name__} does not have {fn_name} method.')
    layernames = list(set(layernames))
    return layernames


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
                f'Module {m.__name__} does not have {fn_name} method.')


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
                f'Module {m.__name__} does not have {fn_name} method.')

    last_task = _get_layer_last_task(username, layername)
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
        if task_name not in TASKS_TO_LAYER_INFO_KEYS:
            continue
        for linfo_key in TASKS_TO_LAYER_INFO_KEYS[task_name]:
            partial_info[linfo_key] = source_state

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
    active_sources = get_sources()
    fn_name = 'update_layer'
    for m in active_sources:
        fn = getattr(m, fn_name, None)
        if fn is not None:
            fn(username, layername, layerinfo)
        else:
            current_app.logger.warn(
                f'Module {m.__name__} does not have {fn_name} method.')


POST_TASKS = [
    db.tasks.import_layer_vector_file,
    geoserver.tasks.publish_layer_from_db,
    geoserver.tasks.create_layer_style,
    filesystem.tasks.generate_layer_thumbnail,
]


def post_layer(username, layername, task_options, use_chunk_upload):
    post_tasks = POST_TASKS.copy()
    if use_chunk_upload:
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
        'by_name': {},
        'by_order': []
    }
    for post_task in reversed(post_tasks):
        tinfo['by_name'][post_task.name] = res
        tinfo['by_order'].insert(0, res)
        res = res.parent
    layer_tasks.append(tinfo)


def put_layer(username, layername, delete_from, task_options, use_chunk_upload):
    if delete_from == 'layman.layer.filesystem.input_files':
        start_idx = 0
    elif delete_from == 'layman.layer.geoserver.sld':
        start_idx = 2
    else:
        raise Exception('Unsupported delete_from='+delete_from)

    put_tasks = POST_TASKS[start_idx:]
    if use_chunk_upload:
        put_tasks.insert(0, filesystem.tasks.wait_for_upload)

    put_chain = chain(*list(map(
        lambda t: _get_task_signature(username, layername, task_options, t),
        put_tasks
    )))
    # res = put_chain.apply_async()
    res = put_chain()

    layer_tasks = _get_layer_tasks(username, layername)
    tinfo = {
        'last': res,
        'by_name': {},
        'by_order': []
    }
    for post_task in reversed(put_tasks):
        tinfo['by_name'][post_task.name] = res
        tinfo['by_order'].insert(0, res)
        res = res.parent
    layer_tasks.append(tinfo)


TASKS_TO_LAYER_INFO_KEYS = {
    'layman.layer.filesystem.input_files.wait_for_upload': ['file'],
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
                f'Module {m.__name__} does not have {fn_name} method.')
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


def _is_task_successful(task_info):
    return task_info['last'].successful()


def _is_task_failed(task_info):
    return any(tr.failed() for tr in task_info['by_order'])


def _is_task_ready(task_info):
    return _is_task_successful(task_info) or _is_task_failed(task_info)