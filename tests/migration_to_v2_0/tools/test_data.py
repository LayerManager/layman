from dataclasses import dataclass

from .client import LAYER_TYPE

USER_1 = 'test_migrate_2_user_1'

USERS = [
    USER_1,
]


@dataclass
class Publication:
    type: str
    workspace: str
    name: str
    owner: str
    rest_args: dict


LAYER_1 = Publication(type=LAYER_TYPE,
                      workspace=USER_1,
                      name='simple_layer',
                      owner=USER_1,
                      rest_args={},
                      )

PUBLICATIONS = [
    LAYER_1,
]


UUID_FILE_PATH = 'tmp/migration_to_v2_0/uuids.json'
