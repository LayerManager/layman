import pytest
from test_tools import process

pytest.register_assert_rewrite('test_tools')

ensure_layman_session = process.ensure_layman_session
liferay_mock = process.liferay_mock
ensure_layman = process.ensure_layman
ensure_layman_module = process.ensure_layman_module
