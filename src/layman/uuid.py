from uuid import UUID, uuid4

from flask import current_app

from layman import LaymanError
from redis import WatchError
from . import settings
from .util import get_modules_from_names, get_providers_from_source_names, call_modules_fn

UUID_SET_KEY = f'{__name__}:UUID_SET'
UUID_METADATA_KEY = f'{__name__}:UUID_METADATA:{{uuid}}'
USER_TYPE_NAMES_KEY = f'{__name__}:USER_TYPE_NAMES:{{username}}:{{publication_type}}'


def import_uuids_to_redis():
    current_app.logger.info('Importing UUIDs to REDIS')
    all_sources = []
    for publ_module in get_modules_from_names(settings.PUBLICATION_MODULES):
        for type_def in publ_module.PUBLICATION_TYPES.values():
            all_sources += type_def['internal_sources']
    providers = get_providers_from_source_names(all_sources)
    results = call_modules_fn(providers, 'get_usernames')
    usernames = []
    for r in results:
        usernames += r
    usernames = list(set(usernames))

    for username in usernames:
        for publ_module in get_modules_from_names(settings.PUBLICATION_MODULES):
            for type_def in publ_module.PUBLICATION_TYPES.values():
                publ_type_name = type_def['type']
                sources = get_modules_from_names(type_def['internal_sources'])
                results = call_modules_fn(sources, 'get_publication_names', [username, publ_type_name])
                pubnames = []
                for r in results:
                    pubnames += r
                pubnames = list(set(pubnames))

                for publ_name in pubnames:
                    results = call_modules_fn(sources, 'get_publication_uuid',
                                              [username, publ_type_name, publ_name])
                    uuid_str = None
                    for maybe_uuid in results:
                        if not isinstance(maybe_uuid, str):
                            continue
                        try:
                            UUID(maybe_uuid)
                            uuid_str = maybe_uuid
                        except ValueError:
                            continue
                    if uuid_str is not None:
                        register_publication_uuid(username, publ_type_name,
                                                  publ_name, uuid_str,
                                                  ignore_duplicate=True)

                        current_app.logger.info(
                            f'Import publication into redis: user {username}, type {publ_type_name}, name {publ_name}, uuid {uuid_str}')


def generate_uuid():
    return str(uuid4())


def register_publication_uuid(username, publication_type, publication_name, uuid_str=None, ignore_duplicate=False):
    if uuid_str is None:
        uuid_str = generate_uuid()

    user_type_names_key = get_user_type_names_key(username, publication_type)
    uuid_metadata_key = get_uuid_metadata_key(uuid_str)

    with settings.LAYMAN_REDIS.pipeline() as pipe:
        while True:
            try:
                pipe.watch(UUID_SET_KEY, uuid_metadata_key, user_type_names_key)

                if not ignore_duplicate:
                    if pipe.sismember(UUID_SET_KEY, uuid_str):
                        raise LaymanError(23, {'message': f'Redis already contains UUID {uuid_str}'})

                    if pipe.exists(uuid_metadata_key):
                        raise LaymanError(23, {'message': f'Redis already contains metadata of UUID {uuid_str}'})

                    if pipe.hexists(user_type_names_key, publication_name):
                        raise LaymanError(23, {
                            'message': f'Redis already contains publication type/user/name {publication_type}/{username}/{publication_name}'})

                pipe.multi()
                pipe.sadd(UUID_SET_KEY, uuid_str)
                pipe.hmset(
                    uuid_metadata_key,
                    {
                        'username': username,
                        'publication_type': publication_type,
                        'publication_name': publication_name,
                    }
                )
                pipe.hset(
                    user_type_names_key,
                    publication_name,
                    uuid_str
                )
                pipe.execute()
                break
            except WatchError:
                continue

    return uuid_str


def delete_publication_uuid(username, publication_type, publication_name, uuid_str):

    user_type_names_key = get_user_type_names_key(username, publication_type)
    uuid_metadata_key = get_uuid_metadata_key(uuid_str)

    settings.LAYMAN_REDIS.srem(UUID_SET_KEY, uuid_str)
    settings.LAYMAN_REDIS.delete(uuid_metadata_key)
    settings.LAYMAN_REDIS.hdel(user_type_names_key, publication_name)


def get_uuid_metadata_key(uuid_str):
    return UUID_METADATA_KEY.format(uuid=uuid_str)


def get_user_type_names_key(username, publication_type):
    return USER_TYPE_NAMES_KEY.format(
        username=username,
        publication_type=publication_type,
    )


def is_valid_uuid(maybe_uuid_str):
    try:
        UUID(maybe_uuid_str)
    except ValueError:
        return False
    return True