from flask import current_app
from layman import settings


REDIS_CURRENT_TASKS = f"{__name__}:CURRENT_TASKS"


def task_prerun(task_name, username, publication_name):
    # current_app.logger.info(f"PRE task={task_name}, username={username}, publication_name={publication_name}")
    redis = settings.LAYMAN_REDIS
    key = REDIS_CURRENT_TASKS
    task_hash = _get_task_hash(task_name, username, publication_name)
    redis.sadd(key, task_hash)


def task_postrun(task_name, username, publication_name):
    # current_app.logger.info(f"POST task={task_name}, username={username}, publication_name={publication_name}")
    redis = settings.LAYMAN_REDIS
    key = REDIS_CURRENT_TASKS
    task_hash = _get_task_hash(task_name, username, publication_name)
    redis.srem(key, task_hash)


def _get_task_hash(task_name, username, publication_name):
    return f"{task_name}:{username}:{publication_name}"


def is_task_running(task_name, username, publication_name=None):
    redis = settings.LAYMAN_REDIS
    key = REDIS_CURRENT_TASKS
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