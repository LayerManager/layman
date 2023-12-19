import pytest

from layman import settings
from . import layman_users_and_roles_to_geoserver_roles


@pytest.mark.parametrize('layman_users_and_roles, exp_geoserver_roles', [
    pytest.param({'username'}, {'USER_USERNAME'}, id='username'),
    pytest.param({'ROLE'}, {'ROLE'}, id='rolename'),
    pytest.param({settings.RIGHTS_EVERYONE_ROLE}, {'ROLE_ANONYMOUS', 'ROLE_AUTHENTICATED'}, id='everyone-role'),
    pytest.param({f'username2', 'ROLE2', settings.RIGHTS_EVERYONE_ROLE}, {'USER_USERNAME2', 'ROLE2', 'ROLE_ANONYMOUS', 'ROLE_AUTHENTICATED'}, id='everything'),
])
def test_layman_users_and_roles_to_geoserver_roles(layman_users_and_roles, exp_geoserver_roles):
    result = layman_users_and_roles_to_geoserver_roles(layman_users_and_roles)
    assert result == exp_geoserver_roles
