from collections import namedtuple

import pytest
pytest.register_assert_rewrite('tests.asserts', 'tests.static_data.data')


Action = namedtuple('ActionTypeDef', ['method', 'params', ])
Publication = namedtuple('PublicationTypeDef', ['workspace', 'type', 'name'])
