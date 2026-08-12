import json
import importlib
import time

import celery.exceptions
from flask import current_app
from celery import states
from celery.contrib.abortable import AbortableAsyncResult, ABORTED

from layman.publication_relation.util import update_related_publications_after_change
from layman import settings, common
from layman.common import redis as redis_util

REDIS_CURRENT_TASK_NAMES = f"{__name__}:CURRENT_TASK_NAMES"
PUBLICATION_CHAIN_INFOS = f'{__name__}:PUBLICATION_CHAIN_INFOS'
LAST_TASK_ID_IN_CHAIN_TO_PUBLICATION = f'{__name__}:LAST_TASK_ID_IN_CHAIN_TO_PUBLICATION'
RUN_AFTER_CHAIN = f'{__name__}:RUN_AFTER_CHAIN'


def _is_layer_task(task_name):
    from layman.layer import LAYER_TYPE
    return task_name.startswith(LAYER_TYPE)


def task_prerun(uuid, _task_id, task_name):
    current_app.logger.info(f"PRE task={task_name}, publication_uuid={uuid}")
    rds = settings.LAYMAN_REDIS
    key = REDIS_CURRENT_TASK_NAMES
    task_hash = _get_task_hash(task_name, uuid)
    rds.sadd(key, task_hash)


def task_postrun(uuid, task_id, task_name, task_state):
    current_app.logger.info(f"POST task={task_name}, publication_uuid={uuid}")
    rds = settings.LAYMAN_REDIS
    key = REDIS_CURRENT_TASK_NAMES
    task_hash = _get_task_hash(task_name, uuid)
    rds.srem(key, task_hash)

    key = LAST_TASK_ID_IN_CHAIN_TO_PUBLICATION
    hash = task_id
    if rds.hexists(key, hash):
        # 'finish_publication_chain' has to run before next_task's 'method' as 'method' expects the publication to be unlocked and
        #   'finish_publication_chain' releases the lock.
        # 'finish_publication_chain' has to run before 'update_related_publications_after_change' as otherwise deadlock arises.
        finish_publication_chain(task_id, task_state)
        if _is_layer_task(task_name):
            from layman.layer.layer_class import Layer
            update_related_publications_after_change(Layer(uuid=uuid))
        run_next_chain(uuid)
    elif task_state == 'FAILURE':
        chain_info = get_publication_chain_info_dict(uuid)
        if chain_info is not None:
            last_task_id = chain_info['last']
            clear_steps_to_run_after_chain(uuid)
            finish_publication_chain(last_task_id, task_state)
            if _is_layer_task(task_name):
                from layman.layer import util
                from layman.layer.layer_class import Layer
                layer = Layer(uuid=uuid)
                util.set_wfs_wms_status_after_fail(layer.workspace, layer.name)


def _get_task_hash(task_name, uuid):
    return f"{task_name}:{uuid}"


def push_step_to_run_after_chain(uuid, step_code):
    rds = settings.LAYMAN_REDIS
    key = RUN_AFTER_CHAIN
    hash = uuid
    val = rds.hget(key, hash)
    queue = json.loads(val) if val is not None else []
    if step_code not in queue:
        queue.append(step_code)
        rds.hset(key, hash, json.dumps(queue))


def pop_step_to_run_after_chain(uuid):
    rds = settings.LAYMAN_REDIS
    key = RUN_AFTER_CHAIN
    hash = uuid
    val = rds.hget(key, hash)
    result = None
    if val:
        queue = json.loads(val)
        if len(queue) > 0:
            result = queue.pop(0)
            rds.hset(key, hash, json.dumps(queue))
    return result


def get_run_after_chain_queue(uuid):
    rds = settings.LAYMAN_REDIS
    key = RUN_AFTER_CHAIN
    hash = uuid
    val = rds.hget(key, hash)
    queue = json.loads(val) if val is not None else []
    return queue


def clear_steps_to_run_after_chain(uuid):
    rds = settings.LAYMAN_REDIS
    key = RUN_AFTER_CHAIN
    hash = uuid
    rds.hdel(key, hash)


def set_publication_chain_finished(uuid, state):
    chain_info = get_publication_chain_info_dict(uuid)
    chain_info['finished'] = True
    chain_info['state'] = state
    set_publication_chain_info_dict(uuid, chain_info)


def finish_publication_chain(last_task_id_in_chain, state):
    rds = settings.LAYMAN_REDIS
    key = LAST_TASK_ID_IN_CHAIN_TO_PUBLICATION
    hash = last_task_id_in_chain
    publ_hash = rds.hget(key, hash)
    if publ_hash is None:
        return
    rds.hdel(key, hash)
    set_publication_chain_finished(publ_hash, state)

    lock = redis_util.get_publication_lock(publ_hash)
    if lock in [common.REQUEST_METHOD_PATCH, common.REQUEST_METHOD_POST, common.PUBLICATION_LOCK_FEATURE_CHANGE, ]:
        redis_util.unlock_publication(publ_hash)


def is_task_running(task_name, uuid=None):
    redis = settings.LAYMAN_REDIS
    key = REDIS_CURRENT_TASK_NAMES
    if uuid is not None:
        task_hash = _get_task_hash(task_name, uuid)
        result = redis.sismember(key, task_hash)
    else:
        hashes = redis.smembers(key)
        result = any((
            h for h in hashes
            if h.startswith(f"{task_name}:")
        ))
    return result


def to_chain_info_with_states(chain_info):
    return {
        **chain_info,
        'last': chain_info['last'].state,
        'by_name': {k: v.state for k, v in chain_info['by_name'].items()},
        'by_order': [t.state for t in chain_info['by_order']],
    }


def get_publication_chain_info_dict(uuid):
    rds = settings.LAYMAN_REDIS
    key = PUBLICATION_CHAIN_INFOS
    hash = uuid
    val = rds.hget(key, hash)
    chain_info = json.loads(val) if val is not None else val
    return chain_info


def get_publication_chain_info(uuid):
    chain_info = get_inconsistent_publication_chain_info(uuid)
    if chain_info and chain_info['finished'] is False and is_chain_ready(chain_info):
        # wait for task_postrun to finish all task-related actions and set 'finished' to True
        attempt = 0
        max_attempts = 20
        while chain_info['finished'] is False and attempt < max_attempts:
            time.sleep(0.1)
            chain_info = get_inconsistent_publication_chain_info(uuid)
            attempt += 1
            if attempt >= max_attempts:
                raise Exception(
                    f"Timeout when waiting for task_postrun to finish in get_publication_chain_info. "
                    f"Attempt={attempt} Chain info={to_chain_info_with_states(chain_info)}")
    return chain_info


def get_inconsistent_publication_chain_info(uuid):
    chain_info = get_publication_chain_info_dict(uuid)
    from layman import celery_app
    if chain_info is not None:
        results = {
            task_id: AbortableAsyncResult(task_id, backend=celery_app.backend)
            for task_id in chain_info['by_order']
        }

        chain_info['by_order'] = [results[task_id] for task_id in chain_info['by_order']]
        chain_info['by_name'] = {
            k: results[task_id] for k, task_id in chain_info['by_name'].items()
        }
        chain_info['last'] = results[chain_info['last']]
    return chain_info


def set_publication_chain_info_dict(uuid, chain_info):
    rds = settings.LAYMAN_REDIS
    val = json.dumps(chain_info)
    key = PUBLICATION_CHAIN_INFOS
    hash = uuid
    rds.hset(key, hash, val)


def set_publication_chain_info(uuid, tasks, task_result):
    if task_result is None:
        return
    chained_results = [task_result]
    prev_result = task_result
    while prev_result.parent is not None:
        prev_result = prev_result.parent
        chained_results.insert(0, prev_result)
    chain_info = {
        'last': task_result.task_id,
        'by_name': {
            tasks[idx].name: r.task_id for idx, r in enumerate(chained_results)
        },
        'by_order': [r.task_id for r in chained_results],
        'finished': False,
        'state': states.PENDING,
    }
    set_publication_chain_info_dict(uuid, chain_info)

    rds = settings.LAYMAN_REDIS
    key = LAST_TASK_ID_IN_CHAIN_TO_PUBLICATION
    val = uuid
    hash = chain_info['last']
    rds.hset(key, hash, val)


def wait_for_abort(uuid):
    round = 0
    max_rounds = 20
    while round <= max_rounds:
        chain_info = get_publication_chain_info_dict(uuid)
        if chain_info['finished']:
            break
        time.sleep(0.5)
        round += 1


def abort_chain(uuid):
    chain_info = get_publication_chain_info(uuid)
    if chain_info is None or is_chain_ready(chain_info):
        return

    abort_task_chain(chain_info['by_order'], chain_info['by_name'])
    wait_for_abort(uuid)
    set_publication_chain_finished(uuid, ABORTED)


def abort_publication_chain(uuid):
    abort_chain(uuid)
    clear_steps_to_run_after_chain(uuid)


def abort_task_chain(results_by_order, results_by_name=None):
    results_by_name = results_by_name or {}
    task_results = [r for r in results_by_order if not r.ready()]
    current_app.logger.info(
        f"Aborting chain of {len(results_by_order)} tasks, {len(task_results)} of them are not yet ready.")

    for task_result in task_results:
        task_name = next((k for k, v in results_by_name.items() if v == task_result), None)
        current_app.logger.info(
            f'processing result {task_name} {task_result.id} {task_result.state} {task_result.ready()} {task_result.successful()} {task_result.failed()}')
        if task_result.ready():
            continue
        prev_task_state = task_result.state
        current_app.logger.info(f'aborting result {task_name} {task_result.id} with state {task_result.state}')
        task_result.abort()
        # Task can finish in the meantime, so SUCCESS is also correct state
        assert task_result.state in (ABORTED, states.FAILURE, states.SUCCESS), f"task_result.state={task_result.state}"
        if prev_task_state == 'STARTED':
            current_app.logger.info(
                f'waiting for result of {task_name} {task_result.id} with state {task_result.state}')
            # if hangs forever, see comment in src/layman/layer/rest_workspace_test.py::test_post_layers_simple
            try:
                task_result.get(propagate=False, timeout=2)
            except celery.exceptions.TimeoutError:
                pass
        current_app.logger.info(f'aborted result {task_name} {task_result.id} with state {task_result.state}')


def is_chain_successful(chain_info):
    # checking 'state' is needed, because celery forgets after some time information about finished tasks
    return chain_info['state'] == states.SUCCESS or chain_info['last'].successful()


def is_chain_failed(chain_info):
    # checking 'state' is needed, because celery forgets after some time information about finished tasks
    return chain_info['state'] == states.FAILURE or any(tr.failed() for tr in chain_info['by_order'])


def is_chain_ready(chain_info):
    # checking 'state' is needed, because celery forgets after some time information about finished tasks
    return chain_info['state'] in {states.SUCCESS, states.FAILURE, ABORTED} or is_chain_successful(chain_info) or \
        is_chain_failed(chain_info)


def is_chain_failed_without_info(chain_info):
    return chain_info['finished'] is True and chain_info['state'] == states.FAILURE and \
        not any(res.state == states.FAILURE for res in chain_info['by_order'])


def delete_publication(uuid):
    chain_info = get_publication_chain_info_dict(uuid)
    if chain_info is None:
        return
    task_id = chain_info['last']

    rds = settings.LAYMAN_REDIS
    key = PUBLICATION_CHAIN_INFOS
    hash = uuid
    rds.hdel(key, hash)

    key = LAST_TASK_ID_IN_CHAIN_TO_PUBLICATION
    rds.hdel(key, task_id)


def run_next_chain(uuid):
    next_task = pop_step_to_run_after_chain(uuid)
    if next_task:
        module_name, method_name = next_task.split('::')
        module = importlib.import_module(module_name)
        method = getattr(module, method_name)
        method(uuid)


class AbortedException(Exception):
    pass
