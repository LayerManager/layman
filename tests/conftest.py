from test_tools import process


liferay_mock = process.liferay_mock
ensure_layman = process.ensure_layman
ensure_layman_module = process.ensure_layman_module


def pytest_addoption(parser):
    parser.addoption(
        "--nocleanup", action="store_true", default=False, help="do not delete publications after tests"
    )
