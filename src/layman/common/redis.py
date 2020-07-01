from flask import request, g, current_app
from functools import wraps
from layman import settings
from layman import LaymanError

PUBLICATION_LOCKS_KEY = f'{__name__}:PUBLICATION_LOCKS'


def create_lock_decorator(publication_type, publication_name_key, error_code, is_task_ready_fn):
    def lock_decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            username = request.view_args['username']
            publication_name = request.view_args[publication_name_key]
            check_http_method(username, publication_type, publication_name, error_code)
            lock_publication(username, publication_type, publication_name, request.method)
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


def get_publication_lock(username, publication_type, publication_name):
    rds = settings.LAYMAN_REDIS
    key = PUBLICATION_LOCKS_KEY
    hash = _get_publication_hash(username, publication_type, publication_name)
    return rds.hget(key, hash)


def lock_publication(username, publication_type, publication_name, lock_method):
    current_app.logger.info(f"Locking {username}:{publication_type}:{publication_name} with {lock_method.upper()}")
    rds = settings.LAYMAN_REDIS
    key = PUBLICATION_LOCKS_KEY
    hash = _get_publication_hash(username, publication_type, publication_name)
    value = lock_method.lower()
    rds.hset(key, hash, value)


def unlock_publication(username, publication_type, publication_name):
    current_app.logger.info(f"Unlocking {username}:{publication_type}:{publication_name}")
    rds = settings.LAYMAN_REDIS
    key = PUBLICATION_LOCKS_KEY
    hash = _get_publication_hash(username, publication_type, publication_name)
    rds.hdel(key, hash)


def check_http_method(username, publication_type, publication_name, error_code):
    current_lock = get_publication_lock(
        username,
        publication_type,
        publication_name,
    )
    if current_lock is None:
        return
    method = request.method.lower()
    if method not in ['patch', 'delete']:
        raise Exception(f"Unknown method to check: {method}")
    if current_lock not in ['patch', 'delete', 'post']:
        raise Exception(f"Unknown current lock: {current_lock}")
    if current_lock in ['patch', 'post']:
        if method in ['patch', 'post']:
            raise LaymanError(error_code)
    elif current_lock in ['delete']:
        if method in ['patch', 'post']:
            raise LaymanError(error_code)


def _get_publication_hash(username, publication_type, publication_name):
    hash = f"{username}:{publication_type}:{publication_name}"
    return hash
