from uuid import UUID, uuid4

from flask import current_app
from . import settings
from .util import get_modules_from_names, get_providers_from_source_names, call_modules_fn

UUID_SET_KEY = 'layman.uuid.set'
UUID_METADATA_KEY_PREFIX = 'layman.uuid.'


def import_uuids_to_redis():
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
    # current_app.logger.info(f'usernames: {usernames}')
    #
    # current_app.logger.info(f'settings.LAYMAN_REDIS.keys("*") {sorted(settings.LAYMAN_REDIS.keys("*"))}')
    # current_app.logger.info(f'settings.LAYMAN_REDIS.keys("*") {len(settings.LAYMAN_REDIS.keys("*"))}')
    # current_app.logger.info(f'settings.LAYMAN_REDIS.keys("celery-task-meta-") {len(settings.LAYMAN_REDIS.keys("celery-task-meta-*"))}')
    # current_app.logger.info(f'settings.LAYMAN_REDIS.keys("layman.") {len(settings.LAYMAN_REDIS.keys("layman.*"))}')
    # current_app.logger.info(f'settings.LAYMAN_REDIS.get({UUID_SET_KEY}) {settings.LAYMAN_REDIS.smembers(UUID_SET_KEY)}')

    for publ_module in get_modules_from_names(settings.PUBLICATION_MODULES):
        for type_def in publ_module.PUBLICATION_TYPES.values():
            publ_type_name = type_def['type']
            sources = get_modules_from_names(type_def['internal_sources'])
            for username in usernames:
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
                                                  publ_name, uuid_str)

                        current_app.logger.info(
                            f'Import publication into redis: user {username}, type {publ_type_name}, name {publ_name}, uuid {uuid_str}')


def generate_uuid():
    return str(uuid4())


def register_publication_uuid(username, publication_type, publication_name, uuid_str=None):
    if uuid_str is None:
        uuid_str = generate_uuid()

    settings.LAYMAN_REDIS.sadd(UUID_SET_KEY, uuid_str)
    settings.LAYMAN_REDIS.hmset(
        f'{UUID_METADATA_KEY_PREFIX}{uuid_str}',
        {
            'user_name': username,
            'publication_type': publication_type,
            'publication_name': publication_name,
        }
    )

    return uuid_str


def delete_publication_uuid(uuid_str):
    settings.LAYMAN_REDIS.srem(UUID_SET_KEY, uuid_str)
    removed_keys = settings.LAYMAN_REDIS.delete(
        f'{UUID_METADATA_KEY_PREFIX}{uuid_str}'
    )
    return True if removed_keys>0 else False
