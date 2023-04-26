from test_tools import process, external_db


oauth2_provider_mock = process.oauth2_provider_mock
ensure_layman = process.ensure_layman
ensure_layman_module = process.ensure_layman_module
ensure_external_db = external_db.ensure_db


def pytest_addoption(parser):
    parser.addoption(
        "--nocleanup", action="store_true", default=False, help="do not delete publications after tests"
    )
