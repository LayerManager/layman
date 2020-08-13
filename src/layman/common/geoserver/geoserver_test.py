import pytest
from .. import geoserver as common
from layman import app

TEST_ROLE = 'test_role_abc'
TEST_USER = 'test_user_abc'
TEST_USER_PASSWORD = 'test_user_abc_pwd'
TEST_WMS_SRS_LIST = [3035]
TEST_PROXY_BASE_URL = 'https://example.com/geoserver/'


@pytest.fixture(scope="module", autouse=True)
def app_context():
    with app.app_context() as ctx:
        yield


@pytest.fixture()
def gs_user():
    usernames = common.get_usernames()
    assert TEST_USER not in usernames
    assert common.ensure_user(TEST_USER, TEST_USER_PASSWORD)
    yield TEST_USER, TEST_USER_PASSWORD
    assert common.delete_user(TEST_USER)


@pytest.fixture()
def gs_role():
    roles = common.get_roles()
    assert TEST_ROLE not in roles
    assert common.ensure_role(TEST_ROLE)
    yield TEST_ROLE
    assert common.delete_role(TEST_ROLE)


def test_role_management():
    init_roles = common.get_roles()
    new_role = TEST_ROLE
    assert new_role not in init_roles
    assert common.ensure_role(new_role)
    roles = common.get_roles()
    assert new_role in roles
    assert len(init_roles) + 1 == len(roles)
    assert common.delete_role(new_role)
    roles = common.get_roles()
    assert new_role not in roles
    assert len(init_roles) == len(roles)


def test_user_management():
    init_usernames = common.get_usernames()
    new_user = TEST_USER
    new_user_pwd = TEST_USER_PASSWORD
    assert new_user not in init_usernames
    assert common.ensure_user(new_user, new_user_pwd)
    usernames = common.get_usernames()
    assert new_user in usernames
    assert len(init_usernames) + 1 == len(usernames)
    assert common.delete_user(new_user)
    usernames = common.get_usernames()
    assert new_user not in [u['userName'] for u in users]
    assert len(init_usernames) == len(usernames)


def test_user_role_management(gs_user, gs_role):
    user = gs_user[0]
    init_user_roles = common.get_user_roles(user)
    role = gs_role
    assert role not in init_user_roles
    assert common.ensure_user_role(user, role)
    user_roles = common.get_user_roles(user)
    assert role in user_roles
    assert len(init_user_roles) + 1 == len(user_roles)
    assert common.delete_user_role(user, role)
    user_roles = common.get_user_roles(user)
    assert role not in user_roles
    assert len(init_user_roles) == len(user_roles)


def test_wms_srs_list_management():
    init_wms_srs_list = common.get_wms_srs_list()
    new_wms_srs_list = TEST_WMS_SRS_LIST
    assert set(init_wms_srs_list) != set(new_wms_srs_list)
    assert common.ensure_wms_srs_list(new_wms_srs_list)
    wms_srs_list = common.get_wms_srs_list()
    assert set(wms_srs_list) == set(new_wms_srs_list)
    assert common.ensure_wms_srs_list(init_wms_srs_list)
    wms_srs_list = common.get_wms_srs_list()
    assert set(wms_srs_list) == set(init_wms_srs_list)


def test_proxy_base_url_management():
    init_proxy_base_url = common.get_proxy_base_url()
    new_proxy_base_url = TEST_PROXY_BASE_URL
    assert init_proxy_base_url != new_proxy_base_url
    assert common.ensure_proxy_base_url(new_proxy_base_url)
    proxy_base_url = common.get_proxy_base_url()
    assert proxy_base_url == new_proxy_base_url
    assert common.ensure_proxy_base_url(init_proxy_base_url)
    proxy_base_url = common.get_proxy_base_url()
    assert proxy_base_url == init_proxy_base_url
