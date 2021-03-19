import hashlib
from redis import WatchError

from layman import settings
from .mem import CACHE as MEM_CACHE


def get(key, create_string_value, mem_value_from_string_value, currently_changing):
    cache_results = True
    mem_hash = None
    mem_value = None
    mem_obj = MEM_CACHE.get(key)
    if mem_obj is not None:
        mem_hash = mem_obj['hash']
        mem_value = mem_obj['value']

    value = None
    hash = None
    refresh_mem = False
    mem_timeout = settings.LAYMAN_CACHE_GS_TIMEOUT

    with settings.LAYMAN_REDIS.pipeline() as pipe:
        while True:
            try:
                pipe.watch(key)

                if pipe.exists(key):
                    if mem_hash is not None:
                        redis_hash = pipe.hget(key, 'hash')
                        if redis_hash == mem_hash:
                            value = mem_value
                            hash = mem_hash
                    if value is None:
                        refresh_mem = True
                        mem_timeout = pipe.ttl(key)
                        redis_obj = pipe.hgetall(key)
                        redis_hash = redis_obj['hash']
                        redis_value = redis_obj['value']
                        value = mem_value_from_string_value(redis_value)
                        hash = redis_hash
                else:
                    refresh_mem = True
                    cache_results = cache_results and not currently_changing()
                    redis_value = create_string_value()
                    if redis_value is not None:
                        value = mem_value_from_string_value(redis_value)
                        hash = hashlib.md5(redis_value.encode('utf-8')).hexdigest()
                        cache_results = cache_results and not currently_changing()
                        if cache_results:
                            redis_obj = {
                                'hash': hash,
                                'value': redis_value,
                            }
                            pipe.multi()
                            pipe.hmset(key, redis_obj)
                            pipe.expire(key, settings.LAYMAN_CACHE_GS_TIMEOUT)

                pipe.execute()
                break
            except WatchError:
                continue

    if value is None or not cache_results:
        MEM_CACHE.delete(key)
    elif refresh_mem or value != mem_value or hash != mem_hash:
        mem_obj = {
            'hash': hash,
            'value': value,
        }
        MEM_CACHE.set(key, mem_obj, ttl=mem_timeout)

    return value


def delete(key):
    MEM_CACHE.delete(key)
    settings.LAYMAN_REDIS.delete(key)
