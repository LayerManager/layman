from functools import wraps
from flask import g, request, current_app

from layman import settings, celery as celery_util, common
from layman import LaymanError

PUBLICATION_LOCKS_KEY = f'{__name__}:PUBLICATION_LOCKS'


def create_lock(publication, method):
    method = method.lower()
    solve_locks(publication, method)
    lock_publication(publication.uuid, method)


def create_lock_decorator(is_chain_ready_fn):
    def lock_decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            publication = g.publication

            create_lock(publication, request.method)
            try:
                result = func(*args, **kwargs)
                if is_chain_ready_fn(publication):
                    unlock_publication(publication.uuid)
                    celery_util.run_next_chain(publication.uuid)
            except Exception as exception:
                try:
                    if is_chain_ready_fn(publication):
                        unlock_publication(publication.uuid)
                        celery_util.run_next_chain(publication.uuid)
                finally:
                    unlock_publication(publication.uuid)
                    celery_util.run_next_chain(publication.uuid)
                raise exception

            return result

        return decorated_function
    return lock_decorator


def get_publication_lock(uuid):
    rds = settings.LAYMAN_REDIS
    key = PUBLICATION_LOCKS_KEY
    return rds.hget(key, uuid)


def lock_publication(uuid, lock_method):
    current_app.logger.info(f"Locking publication uuid={uuid} with {lock_method.upper()}")
    rds = settings.LAYMAN_REDIS
    key = PUBLICATION_LOCKS_KEY
    hash = uuid
    value = lock_method.lower()
    rds.hset(key, hash, value)


def unlock_publication(uuid):
    current_app.logger.info(f"Unlocking publication uuid={uuid}")
    rds = settings.LAYMAN_REDIS
    key = PUBLICATION_LOCKS_KEY
    rds.hdel(key, uuid)


def solve_locks(publication, requested_lock):
    current_lock = get_publication_lock(publication.uuid)
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
            celery_util.abort_publication_chain(publication.uuid)
            celery_util.push_step_to_run_after_chain(publication.uuid, 'layman.util::patch_after_feature_change')
