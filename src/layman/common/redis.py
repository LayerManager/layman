from functools import wraps
from flask import request, current_app

from layman import settings, celery as celery_util, common
from layman import LaymanError

PUBLICATION_LOCKS_KEY = f'{__name__}:PUBLICATION_LOCKS'


def create_lock(workspace, publication_type, publication_name, method):
    method = method.lower()
    solve_locks(workspace, publication_type, publication_name, method)
    lock_publication(workspace, publication_type, publication_name, method)


def create_lock_decorator(publication_type, publication_name_key, is_chain_ready_fn):
    def lock_decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            workspace = request.view_args['workspace']
            publication_name = request.view_args[publication_name_key]
            create_lock(workspace, publication_type, publication_name, request.method)
            try:
                result = func(*args, **kwargs)
                if is_chain_ready_fn(workspace, publication_name):
                    unlock_publication(workspace, publication_type, publication_name)
                    celery_util.run_next_chain(workspace, publication_type, publication_name)
            except Exception as exception:
                try:
                    if is_chain_ready_fn(workspace, publication_name):
                        unlock_publication(workspace, publication_type, publication_name)
                        celery_util.run_next_chain(workspace, publication_type, publication_name)
                finally:
                    unlock_publication(workspace, publication_type, publication_name)
                    celery_util.run_next_chain(workspace, publication_type, publication_name)
                raise exception

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


def solve_locks(workspace, publication_type, publication_name, requested_lock):
    current_lock = get_publication_lock(
        workspace,
        publication_type,
        publication_name,
    )
    if current_lock is None:
        return
    if requested_lock not in [common.PUBLICATION_LOCK_PATCH, common.PUBLICATION_LOCK_DELETE,
                              common.PUBLICATION_LOCK_FEATURE_CHANGE, ]:
        raise Exception(f"Unknown method to check: {requested_lock}")
    if current_lock not in [common.PUBLICATION_LOCK_PATCH, common.PUBLICATION_LOCK_DELETE,
                            common.PUBLICATION_LOCK_POST,
                            common.PUBLICATION_LOCK_FEATURE_CHANGE, ]:
        raise Exception(f"Unknown current lock: {current_lock}")
    if current_lock in [common.PUBLICATION_LOCK_PATCH, common.PUBLICATION_LOCK_POST, ]:
        if requested_lock in [common.PUBLICATION_LOCK_PATCH, common.PUBLICATION_LOCK_POST, ]:
            raise LaymanError(49)
    elif current_lock in [common.PUBLICATION_LOCK_DELETE, ]:
        if requested_lock in [common.PUBLICATION_LOCK_PATCH, common.PUBLICATION_LOCK_POST, ]:
            raise LaymanError(49)
    if requested_lock not in [common.PUBLICATION_LOCK_DELETE, ]:
        if requested_lock == common.PUBLICATION_LOCK_FEATURE_CHANGE:
            raise LaymanError(49, private_data={'can_run_later': True})
        if current_lock == common.PUBLICATION_LOCK_FEATURE_CHANGE and requested_lock in [common.REQUEST_METHOD_PATCH, common.REQUEST_METHOD_POST, ]:
            celery_util.abort_publication_chain(workspace, publication_type, publication_name)
            celery_util.push_step_to_run_after_chain(workspace, publication_type, publication_name, 'layman.util::patch_after_feature_change')


def _get_publication_hash(workspace, publication_type, publication_name):
    hash = f"{workspace}:{publication_type}:{publication_name}"
    return hash
