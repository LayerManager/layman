import json
from functools import wraps
from layman import settings


PUBLICATION_LOCK_KEY = f'{__name__}:PUBLICATION_LOCK:{{username}}:{{publication_type}}:{{publication_name}}'


def get_publication_lock(username, publication_type, publication_name):
    rds = settings.LAYMAN_REDIS
    key = _get_publication_lock_key(username, publication_type, publication_name)
    return rds.get(key)


def lock_publication(username, publication_type, publication_name, lock_method):
    rds = settings.LAYMAN_REDIS
    key = _get_publication_lock_key(username, publication_type, publication_name)
    return rds.set(key, lock_method)


def _get_publication_lock_key(username, publication_type, publication_name):
    key = PUBLICATION_LOCK_KEY.format(
        username=username,
        publication_type=publication_type,
        publication_name=publication_name
    )
    return key


def publication_write_decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f'before function {f.__name__}')
        result = f(*args, **kwargs)
        print(f'after function {f.__name__}')
        return result
    return decorated_function


