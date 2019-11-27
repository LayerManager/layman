import json
from flask import current_app
from layman import settings
from celery.contrib.abortable import AbortableAsyncResult


REDIS_CURRENT_TASK_NAMES = f"{__name__}:CURRENT_TASK_NAMES"
PUBLICATION_TASK_INFOS = f'{__name__}:PUBLICATION_TASK_INFOS'


def task_prerun(task_name, username, publication_name):
    current_app.logger.info(f"PRE task={task_name}, username={username}, publication_name={publication_name}")
    redis = settings.LAYMAN_REDIS
    key = REDIS_CURRENT_TASK_NAMES
    task_hash = _get_task_hash(task_name, username, publication_name)
    redis.sadd(key, task_hash)


def task_postrun(task_name, username, publication_name):
    current_app.logger.info(f"POST task={task_name}, username={username}, publication_name={publication_name}")
    redis = settings.LAYMAN_REDIS
    key = REDIS_CURRENT_TASK_NAMES
    task_hash = _get_task_hash(task_name, username, publication_name)
    redis.srem(key, task_hash)


def _get_task_hash(task_name, username, publication_name):
    return f"{task_name}:{username}:{publication_name}"


def is_task_running(task_name, username, publication_name=None):
    redis = settings.LAYMAN_REDIS
    key = REDIS_CURRENT_TASK_NAMES
    if publication_name is not None:
        task_hash = _get_task_hash(task_name, username, publication_name)
        result = redis.sismember(key, task_hash)
    else:
        hashes = redis.smembers(key)
        result = any((
            h for h in hashes
            if h.startswith(f"{task_name}:{username}:")
        ))
    return result


def get_publication_task_info(username, publication_type, publication_name):
    from layman import celery_app
    rds = settings.LAYMAN_REDIS
    key = PUBLICATION_TASK_INFOS
    hash = _get_publication_hash(username, publication_type, publication_name)
    val = rds.hget(key, hash)
    tinfo = json.loads(val) if val is not None else val
    if tinfo is not None:
        results = {
            task_id: AbortableAsyncResult(task_id, backend=celery_app.backend)
            for task_id in tinfo['by_order']
        }

        tinfo['by_order'] = [results[task_id] for task_id in tinfo['by_order']]
        for idx, res in enumerate(tinfo['by_order']):
            if idx > 0 and res.parent is None:
                current_app.logger.warning(f"Parent if result {res.task_id} is None!")
                # res.parent = tinfo['by_order'][idx-1]
        tinfo['by_name'] = {
            k: results[task_id] for k, task_id in tinfo['by_name'].items()
        }
        tinfo['last'] = results[tinfo['last']]
    return tinfo


def set_publication_task_info(username, publication_type, publication_name, tasks, task_result):
    chained_results = [task_result]
    prev_result = task_result
    while prev_result.parent is not None:
        prev_result = prev_result.parent
        chained_results.insert(0, prev_result)
    task_info = {
        'last': task_result.task_id,
        'by_name': {
            tasks[idx].name: r.task_id for idx, r in enumerate(chained_results)
        },
        'by_order': [r.task_id for r in chained_results]
    }
    val = json.dumps(task_info)

    rds = settings.LAYMAN_REDIS
    key = PUBLICATION_TASK_INFOS
    hash = _get_publication_hash(username, publication_type, publication_name)
    return rds.hset(key, hash, val)


def abort_task(task_info):
    if task_info is None or is_task_ready(task_info):
        return
    # todo if all tasks are in pending state, it means that either they did not started yet or their celery already deleted their results
    # if it's the first case, tasks should be revoked instead of aborted
    # generally, if it's pending, revoke it, otherwise abort it

    task_results = [r for r in task_info['by_order'] if not r.ready()]
    for task_result in reversed(task_results):
        task_name = next(k for k,v in task_info['by_name'].items() if v == task_result)
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


def is_task_successful(task_info):
    return task_info['last'].successful()


def is_task_failed(task_info):
    return any(tr.failed() for tr in task_info['by_order'])


def is_task_ready(task_info):
    return is_task_successful(task_info) or is_task_failed(task_info)


def _get_publication_hash(username, publication_type, publication_name):
    hash = f"{username}:{publication_type}:{publication_name}"
    return hash


