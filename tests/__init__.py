from collections import namedtuple
from enum import Enum

import pytest
pytest.register_assert_rewrite('tests.asserts', 'tests.static_data.data')


Action = namedtuple('ActionTypeDef', ['method', 'params', ])
Publication = namedtuple('PublicationTypeDef', ['workspace', 'type', 'name'])
PublicationValues = namedtuple('PublicationValuesDef', ['type', 'definition', 'info_values', 'thumbnail'])


class EnumTestTypes(Enum):
    MANDATORY = 'mandatory'
    OPTIONAL = 'optional'
    IGNORE = 'ignore'


class EnumTestKeys(Enum):
    TYPE = 'TEST_TYPE'
