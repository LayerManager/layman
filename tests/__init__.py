from typing import Optional
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum

import pytest
pytest.register_assert_rewrite('tests.asserts', 'tests.static_data.data')
EXTERNAL_DB_NAME = 'external_test_db'


Action = namedtuple('ActionTypeDef', ['method', 'params', ])
Publication = namedtuple('PublicationTypeDef', ['workspace', 'type', 'name'])


@dataclass(frozen=True)
class PublicationValues:
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
