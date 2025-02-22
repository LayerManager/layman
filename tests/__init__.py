from typing import Optional
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum

import pytest
pytest.register_assert_rewrite('tests.asserts', 'tests.static_data.data')
EXTERNAL_DB_NAME = 'external_test_db'
READ_ONLY_USER = 'read_only_user'


Action = namedtuple('ActionTypeDef', ['method', 'params', ])


@dataclass(frozen=True)
class Publication4Test:
    workspace: str
    type: str
    name: str
    uuid: Optional[str] = None

    def __iter__(self):
        return iter([self.workspace, self.type, self.name])


@dataclass(frozen=True)
class TestPublicationValues:
    type: str
    definition: dict
    info_values: dict
    thumbnail: str
    legend_image: Optional[str] = None


class EnumTestTypes(Enum):
    MANDATORY = 'mandatory'
    OPTIONAL = 'optional'
    IGNORE = 'ignore'


class EnumTestKeys(Enum):
    TYPE = 'TEST_TYPE'
