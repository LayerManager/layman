import pytest

from . import util as gs_util, GS_AUTH

TEST_ROLE = 'test_role_abc'
TEST_USER = 'test_user_abc'
TEST_USER_PASSWORD = 'test_user_abc_pwd'
TEST_SERVICE_SRS_LIST = ['EPSG:3035', 'EPSG:4326']
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


@pytest.mark.parametrize('service', gs_util.SERVICE_TYPES)
def test_service_srs_list_management(service):
    init_service_epsg_codes = gs_util.get_service_srs_list(service, GS_AUTH)
    new_service_srs_list = TEST_SERVICE_SRS_LIST
    new_service_epsg_codes = [gs_util.get_epsg_code(crs) for crs in new_service_srs_list]
    assert set(init_service_epsg_codes) != set(new_service_epsg_codes)
    assert gs_util.ensure_service_srs_list(service, new_service_srs_list, GS_AUTH)
    service_srs_list = gs_util.get_service_srs_list(service, GS_AUTH)
    assert set(service_srs_list) == set(new_service_epsg_codes)
    init_service_crs_list = [f'EPSG:{srid}' for srid in init_service_epsg_codes]
    assert gs_util.ensure_service_srs_list(service, init_service_crs_list, GS_AUTH)
    service_srs_list = gs_util.get_service_srs_list(service, GS_AUTH)
    assert set(service_srs_list) == set(init_service_epsg_codes)


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
