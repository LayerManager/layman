import json
import time
from flask import current_app
from layman import settings
from celery.contrib.abortable import AbortableAsyncResult
from layman.common import redis as redis_util


REDIS_CURRENT_TASK_NAMES = f"{__name__}:CURRENT_TASK_NAMES"
PUBLICATION_TASK_INFOS = f'{__name__}:PUBLICATION_TASK_INFOS'
TASK_ID_TO_PUBLICATION = f'{__name__}:TASK_ID_TO_PUBLICATION'


def task_prerun(username, publication_type, publication_name, task_id, task_name):
    current_app.logger.info(f"PRE task={task_name}, username={username}, publication_name={publication_name}")
    rds = settings.LAYMAN_REDIS
    key = REDIS_CURRENT_TASK_NAMES
    task_hash = _get_task_hash(task_name, username, publication_name)
    rds.sadd(key, task_hash)


def task_postrun(username, publication_type, publication_name, task_id, task_name, task_state):
    current_app.logger.info(f"POST task={task_name}, username={username}, publication_name={publication_name}")
    rds = settings.LAYMAN_REDIS
    key = REDIS_CURRENT_TASK_NAMES
    task_hash = _get_task_hash(task_name, username, publication_name)
    rds.srem(key, task_hash)

    key = TASK_ID_TO_PUBLICATION
    hash = task_id
    if rds.hexists(key, hash):
        finnish_publication_task(task_id)
    elif task_state == 'FAILURE':
        tinfo = get_publication_task_info_dict(username, publication_type, publication_name)
        if tinfo is not None:
            last_task_id = tinfo['last']
            finnish_publication_task(last_task_id)


def _get_task_hash(task_name, username, publication_name):
    return f"{task_name}:{username}:{publication_name}"


def finnish_publication_task(task_id):
    rds = settings.LAYMAN_REDIS
    key = TASK_ID_TO_PUBLICATION
    hash = task_id
    publ_hash = rds.hget(key, hash)
    if publ_hash is None:
        return
    username, publication_type, publication_name = _hash_to_publication(publ_hash)

    tinfo = get_publication_task_info_dict(username, publication_type, publication_name)
    tinfo['finished'] = True
    set_publication_task_info_dict(username, publication_type, publication_name, tinfo)

    rds.hdel(key, hash)

    lock = redis_util.get_publication_lock(username, publication_type, publication_name)
    if lock in ['patch', 'post']:
        redis_util.unlock_publication(username, publication_type, publication_name)


def _hash_to_publication(hash):
    return hash.split(':')


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


def get_publication_task_info_dict(username, publication_type, publication_name):
    rds = settings.LAYMAN_REDIS
    key = PUBLICATION_TASK_INFOS
    hash = _get_publication_hash(username, publication_type, publication_name)
    val = rds.hget(key, hash)
    tinfo = json.loads(val) if val is not None else val
    return tinfo


def get_publication_task_info(username, publication_type, publication_name):
    tinfo = get_publication_task_info_dict(username, publication_type, publication_name)
    from layman import celery_app
    if tinfo is not None:
        results = {
            task_id: AbortableAsyncResult(task_id, backend=celery_app.backend)
            for task_id in tinfo['by_order']
        }

        tinfo['by_order'] = [results[task_id] for task_id in tinfo['by_order']]
        for idx, res in enumerate(tinfo['by_order']):
            if idx > 0 and res.parent is None:
                # this is common behaviour
                pass
                # current_app.logger.warning(f"Parent of result {res.task_id} is None!")
                # res.parent = tinfo['by_order'][idx-1]
        tinfo['by_name'] = {
            k: results[task_id] for k, task_id in tinfo['by_name'].items()
        }
        tinfo['last'] = results[tinfo['last']]
    return tinfo


def set_publication_task_info_dict(username, publication_type, publication_name, task_info):
    rds = settings.LAYMAN_REDIS
    val = json.dumps(task_info)
    key = PUBLICATION_TASK_INFOS
    hash = _get_publication_hash(username, publication_type, publication_name)
    rds.hset(key, hash, val)


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
        'by_order': [r.task_id for r in chained_results],
        'finished': False,
    }
    set_publication_task_info_dict(username, publication_type, publication_name, task_info)

    rds = settings.LAYMAN_REDIS
    key = TASK_ID_TO_PUBLICATION
    val = _get_publication_hash(username, publication_type, publication_name)
    hash = task_info['last']
    rds.hset(key, hash, val)


def abort_task(task_info):
    if task_info is None or is_task_ready(task_info):
        return

    abort_task_chain(task_info['by_order'], task_info['by_name'])
    finnish_publication_task(task_info['last'].task_id)


def abort_task_chain(results_by_order, results_by_name=None):
    results_by_name = results_by_name or {}
    task_results = [r for r in results_by_order if not r.ready()]
    current_app.logger.info(f"Aborting chain of {len(results_by_order)} tasks, {len(task_results)} of them are not yet ready.")

    for task_result in task_results:
        task_name = next((k for k,v in results_by_name.items() if v == task_result), None)
        current_app.logger.info(
            f'processing result {task_name} {task_result.id} {task_result.state} {task_result.ready()} {task_result.successful()} {task_result.failed()}')
        if task_result.ready():
            continue
        prev_task_state = task_result.state
        current_app.logger.info(f'aborting result {task_name} {task_result.id} with state {task_result.state}')
        task_result.abort()
        assert task_result.state == 'ABORTED'
        if prev_task_state == 'STARTED':
            current_app.logger.info(f'waiting for result of {task_name} {task_result.id} with state {task_result.state}')
            task_result.get(propagate=False)
        current_app.logger.info(f'aborted result {task_name} {task_result.id} with state {task_result.state}')


def abort_task_chain__deprecated(results_by_order, results_by_name=None):
    results_by_name = results_by_name or {}
    task_results = [r for r in results_by_order if not r.ready()]
    current_app.logger.info(f"Aborting chain of {len(results_by_order)} tasks, {len(task_results)} of the are not yet ready.")
    results_to_revoke = []
    results_to_abort = []
    for task_result in reversed(task_results):
        task_name = next((k for k,v in results_by_name.items() if v == task_result), None)
        current_app.logger.info(
            f'processing result {task_name} {task_result.id} {task_result.state} {task_result.ready()} {task_result.successful()} {task_result.failed()}')
        if task_result.ready():
            continue
        prev_task_state = task_result.state
        if task_result.state == 'PENDING':
            results_to_revoke.append(task_result)
            current_app.logger.info(f'revoking result {task_name} {task_result.id} with state {task_result.state}')
            # HERE IS THE PROBLEM - sometimes, it hangs forever (with the first processed task result)
            # but I was not able to reproduce it for testing (in other words, in test cases it did not hang)
            task_result.revoke()
            current_app.logger.info(f'result marked as revoked {task_name} {task_result.id} with state {task_result.state}')
        else:
            results_to_abort.append(task_result)
            current_app.logger.info(f'aborting result {task_name} {task_result.id} with state {task_result.state}')
            task_result.abort()
            assert task_result.state == 'ABORTED'
            if prev_task_state == 'STARTED':
                current_app.logger.info(f'waiting for result of {task_name} {task_result.id} with state {task_result.state}')
                task_result.get(propagate=False)
            current_app.logger.info(f'aborted result {task_name} {task_result.id} with state {task_result.state}')

    max_tries = 50
    tries = 1
    results_to_abort.reverse()
    last_aborted_task = results_to_abort[-1] if len(results_to_abort) > 0 else None
    results_to_revoke.reverse()
    first_revoked_result = results_to_revoke[0] if len(results_to_revoke) > 0 else None
    last_aborted_task_successful = last_aborted_task is not None and last_aborted_task.successful()
    if last_aborted_task_successful:
        while first_revoked_result.state != 'REVOKED':
            if tries > max_tries:
                raise Exception(f"Task was not revoked in {max_tries} tries: {first_revoked_result.task_id}={first_revoked_result.state}")
            current_app.logger.info(f'waiting for REVOKED status, try {tries}/{max_tries}')
            time.sleep(0.1)
            tries += 1
    for idx, task_result in enumerate(results_to_revoke):
        assert idx == 0 or task_result.state == 'PENDING'


def is_task_successful(task_info):
    return task_info['last'].successful()


def is_task_failed(task_info):
    return any(tr.failed() for tr in task_info['by_order'])


def is_task_ready(task_info):
    return is_task_successful(task_info) or is_task_failed(task_info) or task_info['finished'] is True


def _get_publication_hash(username, publication_type, publication_name):
    hash = f"{username}:{publication_type}:{publication_name}"
    return hash


def delete_publication(username, publication_type, publication_name):
    tinfo = get_publication_task_info_dict(username, publication_type, publication_name)
    if tinfo is None:
        return
    task_id = tinfo['last']

    rds = settings.LAYMAN_REDIS
    key = PUBLICATION_TASK_INFOS
    hash = _get_publication_hash(username, publication_type, publication_name)
    rds.hdel(key, hash)

    key = TASK_ID_TO_PUBLICATION
    rds.hdel(key, task_id)


class AbortedException(Exception):
    pass
