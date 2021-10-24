import pytest
from test_tools import process

pytest.register_assert_rewrite('test_tools', 'tests')

liferay_mock = process.liferay_mock
ensure_layman = process.ensure_layman


def pytest_addoption(parser):
    parser.addoption(
        "--nocleanup", action="store_true", default=False, help="do not delete publications after tests"
    )
