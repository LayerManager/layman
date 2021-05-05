from functools import wraps
from flask import request, current_app

from layman import settings, celery as celery_util
from layman import LaymanError

PUBLICATION_LOCKS_KEY = f'{__name__}:PUBLICATION_LOCKS'


def create_lock(workspace, publication_type, publication_name, error_code, method):
    method = method.lower()
    solve_locks(workspace, publication_type, publication_name, error_code, method)
    lock_publication(workspace, publication_type, publication_name, method)


def create_lock_decorator(publication_type, publication_name_key, error_code, is_task_ready_fn):
    def lock_decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            username = request.view_args['workspace']
            publication_name = request.view_args[publication_name_key]
            create_lock(username, publication_type, publication_name, error_code, request.method)
            try:
                result = f(*args, **kwargs)
                if is_task_ready_fn(username, publication_name):
                    unlock_publication(username, publication_type, publication_name)
            except Exception as e:
                try:
                    if is_task_ready_fn(username, publication_name):
                        unlock_publication(username, publication_type, publication_name)
                finally:
                    unlock_publication(username, publication_type, publication_name)
                raise e
            return result

        return decorated_function

    return lock_decorator


def get_publication_lock(workspace, publication_type, publication_name):
    rds = settings.LAYMAN_REDIS
    key = PUBLICATION_LOCKS_KEY
    hash = _get_publication_hash(workspace, publication_type, publication_name)
    return rds.hget(key, hash)


def lock_publication(workspace, publication_type, publication_name, lock_method):
    current_app.logger.info(f"Locking {workspace}:{publication_type}:{publication_name} with {lock_method.upper()}")
    rds = settings.LAYMAN_REDIS
    key = PUBLICATION_LOCKS_KEY
    hash = _get_publication_hash(workspace, publication_type, publication_name)
    value = lock_method.lower()
    rds.hset(key, hash, value)


def unlock_publication(workspace, publication_type, publication_name):
    current_app.logger.info(f"Unlocking {workspace}:{publication_type}:{publication_name}")
    rds = settings.LAYMAN_REDIS
    key = PUBLICATION_LOCKS_KEY
    hash = _get_publication_hash(workspace, publication_type, publication_name)
    rds.hdel(key, hash)


def solve_locks(workspace, publication_type, publication_name, error_code, method):
    current_lock = get_publication_lock(
        workspace,
        publication_type,
        publication_name,
    )
    if current_lock is None:
        return
    if method not in ['patch', 'delete', 'wfst', ]:
        raise Exception(f"Unknown method to check: {method}")
    if current_lock not in ['patch', 'delete', 'post', 'wfst', ]:
        raise Exception(f"Unknown current lock: {current_lock}")
    if current_lock in ['patch', 'post']:
        if method in ['patch', 'post']:
            raise LaymanError(error_code)
    elif current_lock in ['delete']:
        if method in ['patch', 'post']:
            raise LaymanError(error_code)
    if method not in ['delete']:
        if (current_lock, method) == ('wfst', 'wfst'):
            chain_info = celery_util.get_publication_chain_info(workspace, publication_type, publication_name)
            celery_util.abort_chain(chain_info)
        else:
            assert current_lock not in ['wfst', ] and method not in ['wfst', ],\
                f'current_lock={current_lock}, method={method},' \
                f'workspace, publication_type, publication_name={(workspace, publication_type, publication_name)}'


def _get_publication_hash(workspace, publication_type, publication_name):
    hash = f"{workspace}:{publication_type}:{publication_name}"
    return hash
