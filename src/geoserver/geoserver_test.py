import pytest

from . import util as gs_util, GS_AUTH

TEST_ROLE = 'test_role_abc'
TEST_USER = 'test_user_abc'
TEST_USER_PASSWORD = 'test_user_abc_pwd'
TEST_SERVICE_SRS_LIST = [3035, 4326]
TEST_PROXY_BASE_URL = 'https://example.com/geoserver/'


@pytest.fixture(scope="module", autouse=True)
def restart_gs():
    yield
    gs_util.reload(GS_AUTH)


@pytest.fixture()
def gs_user():
    usernames = gs_util.get_usernames(GS_AUTH)
    assert TEST_USER not in usernames
    assert gs_util.ensure_user(TEST_USER, TEST_USER_PASSWORD, GS_AUTH)
    yield TEST_USER, TEST_USER_PASSWORD
    assert gs_util.delete_user(TEST_USER, GS_AUTH)


@pytest.fixture()
def gs_role():
    roles = gs_util.get_roles(GS_AUTH)
    assert TEST_ROLE not in roles
    assert gs_util.ensure_role(TEST_ROLE, GS_AUTH)
    yield TEST_ROLE
    assert gs_util.delete_role(TEST_ROLE, GS_AUTH)


def test_role_management():
    init_roles = gs_util.get_roles(GS_AUTH)
    new_role = TEST_ROLE
    assert new_role not in init_roles
    assert gs_util.ensure_role(new_role, GS_AUTH)
    roles = gs_util.get_roles(GS_AUTH)
    assert new_role in roles
    assert len(init_roles) + 1 == len(roles)
    assert gs_util.delete_role(new_role, GS_AUTH)
    roles = gs_util.get_roles(GS_AUTH)
    assert new_role not in roles
    assert len(init_roles) == len(roles)


def test_user_management():
    init_usernames = gs_util.get_usernames(GS_AUTH)
    new_user = TEST_USER
    new_user_pwd = TEST_USER_PASSWORD
    assert new_user not in init_usernames
    assert gs_util.ensure_user(new_user, new_user_pwd, GS_AUTH)
    usernames = gs_util.get_usernames(GS_AUTH)
    assert new_user in usernames
    assert len(init_usernames) + 1 == len(usernames)
    assert gs_util.delete_user(new_user, GS_AUTH)
    usernames = gs_util.get_usernames(GS_AUTH)
    assert new_user not in usernames
    assert len(init_usernames) == len(usernames)


def test_user_role_management(gs_user, gs_role):
    user = gs_user[0]
    init_user_roles = gs_util.get_user_roles(user, GS_AUTH)
    role = gs_role
    assert role not in init_user_roles
    assert gs_util.ensure_user_role(user, role, GS_AUTH)
    user_roles = gs_util.get_user_roles(user, GS_AUTH)
    assert role in user_roles
    assert len(init_user_roles) + 1 == len(user_roles)
    assert gs_util.delete_user_role(user, role, GS_AUTH)
    user_roles = gs_util.get_user_roles(user, GS_AUTH)
    assert role not in user_roles
    assert len(init_user_roles) == len(user_roles)


@pytest.mark.parametrize('service', gs_util.SERVICE_TYPES)
def test_service_srs_list_management(service):
    init_service_srs_list = gs_util.get_service_srs_list(service, GS_AUTH)
    new_service_srs_list = TEST_SERVICE_SRS_LIST
    assert set(init_service_srs_list) != set(new_service_srs_list)
    assert gs_util.ensure_service_srs_list(service, new_service_srs_list, GS_AUTH)
    service_srs_list = gs_util.get_service_srs_list(service, GS_AUTH)
    assert set(service_srs_list) == set(new_service_srs_list)
    assert gs_util.ensure_service_srs_list(service, init_service_srs_list, GS_AUTH)
    service_srs_list = gs_util.get_service_srs_list(service, GS_AUTH)
    assert set(service_srs_list) == set(init_service_srs_list)


def test_proxy_base_url_management():
    init_proxy_base_url = gs_util.get_proxy_base_url(GS_AUTH)
    new_proxy_base_url = TEST_PROXY_BASE_URL
    assert init_proxy_base_url != new_proxy_base_url
    assert gs_util.ensure_proxy_base_url(new_proxy_base_url, GS_AUTH)
    proxy_base_url = gs_util.get_proxy_base_url(GS_AUTH)
    assert proxy_base_url == new_proxy_base_url
    assert gs_util.ensure_proxy_base_url(init_proxy_base_url, GS_AUTH)
    proxy_base_url = gs_util.get_proxy_base_url(GS_AUTH)
    assert proxy_base_url == init_proxy_base_url
