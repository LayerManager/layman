from collections import defaultdict
from uuid import UUID, uuid4

from flask import current_app
from redis import WatchError

from layman import LaymanError, celery as celery_util, util as layman_util
from layman.common import redis as redis_util
from layman.common.prime_db_schema import publications as prime_db_publications
from . import settings

UUID_SET_KEY = f'{__name__}:UUID_SET'
UUID_METADATA_KEY = f'{__name__}:UUID_METADATA:{{uuid}}'
WORKSPACE_TYPE_NAMES_KEY = f'{__name__}:WORKSPACE_TYPE_NAMES:{{workspace}}:{{publication_type}}'


def import_uuids_to_redis():
    current_app.logger.info('Importing UUIDs to REDIS')

    infos = layman_util.get_publication_infos()
    for (workspace, publication_type, publication_name), info in infos.items():
        register_publication_uuid_to_redis(workspace, publication_type,
                                           publication_name, info["uuid"],
                                           ignore_duplicate=True)

        current_app.logger.info(
            f'Import publication into redis: workspace {workspace}, type {publication_type}, name {publication_name}, uuid {info["uuid"]}')


def generate_uuid():
    return str(uuid4())


def register_publication_uuid_to_redis(workspace, publication_type, publication_name, uuid_str=None, ignore_duplicate=False):
    if uuid_str is None:
        uuid_str = generate_uuid()

    workspace_type_names_key = get_workspace_type_names_key(workspace, publication_type)
    uuid_metadata_key = get_uuid_metadata_key(uuid_str)

    with settings.LAYMAN_REDIS.pipeline() as pipe:
        while True:
            try:
                pipe.watch(UUID_SET_KEY, uuid_metadata_key, workspace_type_names_key)

                if not ignore_duplicate:
                    if pipe.sismember(UUID_SET_KEY, uuid_str):
                        raise LaymanError(23, {'message': f'Redis already contains UUID {uuid_str}'})

                    if pipe.exists(uuid_metadata_key):
                        raise LaymanError(23, {'message': f'Redis already contains metadata of UUID {uuid_str}'})

                    if pipe.hexists(workspace_type_names_key, publication_name):
                        raise LaymanError(23, {
                            'message': f'Redis already contains publication type/workspace/name {publication_type}/{workspace}/{publication_name}'})

                pipe.multi()
                pipe.sadd(UUID_SET_KEY, uuid_str)
                pipe.hmset(
                    uuid_metadata_key,
                    {
                        'workspace': workspace,
                        'publication_type': publication_type,
                        'publication_name': publication_name,
                    }
                )
                pipe.hset(
                    workspace_type_names_key,
                    publication_name,
                    uuid_str
                )
                pipe.execute()
                break
            except WatchError:
                continue

    return uuid_str


def delete_publication_uuid_from_redis(workspace, publication_type, publication_name, uuid_str):
    workspace_type_names_key = get_workspace_type_names_key(workspace, publication_type)
    uuid_metadata_key = get_uuid_metadata_key(uuid_str)

    settings.LAYMAN_REDIS.srem(UUID_SET_KEY, uuid_str)
    settings.LAYMAN_REDIS.delete(uuid_metadata_key)
    settings.LAYMAN_REDIS.hdel(workspace_type_names_key, publication_name)


def get_uuid_metadata_key(uuid_str):
    return UUID_METADATA_KEY.format(uuid=uuid_str)


def get_workspace_type_names_key(workspace, publication_type):
    return WORKSPACE_TYPE_NAMES_KEY.format(
        workspace=workspace,
        publication_type=publication_type,
    )


def get_publication_uuid_from_redis(workspace, publication_type, publication_name):
    return settings.LAYMAN_REDIS.hget(
        get_workspace_type_names_key(workspace, publication_type),
        publication_name,
    )


def get_uuid_metadata_from_redis(uuid_str):
    return settings.LAYMAN_REDIS.hgetall(get_uuid_metadata_key(uuid_str))


def get_publication_from_redis(workspace, publication_type, publication_name):
    uuid = get_publication_uuid_from_redis(workspace, publication_type, publication_name)
    return _publication_from_identity(uuid, workspace, publication_type, publication_name)


def get_publication_from_redis_by_uuid(uuid):
    metadata = get_uuid_metadata_from_redis(uuid)
    return _publication_from_identity(
        uuid,
        metadata['workspace'],
        metadata['publication_type'],
        metadata['publication_name'],
    )


def _publication_from_identity(uuid, workspace, publication_type, publication_name):
    from layman.layer import LAYER_TYPE
    from layman.layer.layer_class import Layer
    from layman.map.map_class import Map
    if publication_type == LAYER_TYPE:
        return Layer(uuid=uuid, layer_tuple=(workspace, publication_name), load=False)
    return Map(uuid=uuid, map_tuple=(workspace, publication_name), load=False)


def is_valid_uuid(maybe_uuid_str):
    try:
        UUID(maybe_uuid_str)
    except ValueError:
        return False
    return True


def check_redis_consistency(expected_publ_num_by_type=None):
    # get info from non-redis sources
    infos = layman_util.get_publication_infos()
    num_total_publs = len(infos)
    total_publs = list(infos.keys())

    # publication types and names
    redis = settings.LAYMAN_REDIS
    workspace_publ_keys = redis.keys(':'.join(WORKSPACE_TYPE_NAMES_KEY.split(':')[:2]) + ':*')
    uuid_keys = redis.keys(':'.join(UUID_METADATA_KEY.split(':')[:2]) + ':*')
    assert num_total_publs == len(uuid_keys), f"total_publs={total_publs}, uuid_keys={uuid_keys}"

    total_publs_by_type = defaultdict(list)
    for publ in total_publs:
        total_publs_by_type[publ[1]].append((publ[0], publ[2]))

    if expected_publ_num_by_type is not None:
        for publ_type, publ_num in expected_publ_num_by_type.items():
            found_publ_num = len(total_publs_by_type[publ_type])
            assert publ_num == found_publ_num, f"expected {publ_num} of {publ_type}, found {found_publ_num}: {total_publs}"

    num_publ = 0
    for workspace_publ_key in workspace_publ_keys:
        num_publ += redis.hlen(workspace_publ_key)
    assert num_publ == len(uuid_keys)

    # publication uuids
    uuids = redis.smembers(UUID_SET_KEY)
    assert len(uuids) == num_publ

    for uuid_str in uuids:
        assert get_uuid_metadata_key(uuid_str) in uuid_keys

    for uuid_key in uuid_keys:
        uuid_dict = redis.hgetall(uuid_key)
        assert redis.hexists(
            get_workspace_type_names_key(
                uuid_dict['workspace'],
                uuid_dict['publication_type']
            ),
            uuid_dict['publication_name'],
        )

    # publication tasks
    chain_infos_len = redis.hlen(celery_util.PUBLICATION_CHAIN_INFOS)
    assert chain_infos_len == len(total_publs), f"task_infos_len={chain_infos_len}, total_publs={total_publs}"

    task_hashes = redis.smembers(celery_util.REDIS_CURRENT_TASK_NAMES)

    for workspace, publ_type_name, pubname in total_publs:
        publication = _publication_from_identity(
            infos[(workspace, publ_type_name, pubname)]['uuid'],
            workspace,
            publ_type_name,
            pubname,
        )
        chain_info = celery_util.get_publication_chain_info(publication)
        is_ready = celery_util.is_chain_ready(chain_info)
        assert chain_info['finished'] is is_ready
        assert (next((
            task_hash for task_hash in task_hashes
            if task_hash.endswith(f':{publication.uuid}')
        ), None) is None) is is_ready, f"{workspace}, {publ_type_name}, {pubname}: {is_ready}, {task_hashes}"
        assert (redis.hget(celery_util.LAST_TASK_ID_IN_CHAIN_TO_PUBLICATION, chain_info['last'].task_id) is None) is is_ready

    # publication locks
    locks = redis.hgetall(redis_util.PUBLICATION_LOCKS_KEY)
    assert len(locks) == len(task_hashes), f"{locks} != {task_hashes}"
    for k, _ in locks.items():
        assert next((
            task_hash for task_hash in task_hashes
            if task_hash.endswith(f':{k}')
        ), None) is not None
    return total_publs_by_type


def check_input_uuid(uuid):
    if uuid:
        if not is_valid_uuid(uuid):
            raise LaymanError(2, {'parameter': 'uuid', 'message': f'UUID `{uuid}` is not valid uuid', })
        publications_by_uuid = prime_db_publications.get_publication_infos(uuid=uuid)
        if publications_by_uuid:
            raise LaymanError(2, {'parameter': 'uuid', 'message': f'UUID `{uuid}` value already in use', })
