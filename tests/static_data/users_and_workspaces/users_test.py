import pytest

from geoserver import util as gs_util
from layman import settings
from test_tools import process_client
from ... import static_data as data


@pytest.mark.parametrize('username', data.USERS)
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman')
def test_geoserver(username):
    process_client.ensure_reserved_username(username)

    auth = settings.LAYMAN_GS_AUTH
    gs_usernames = gs_util.get_usernames(auth)
    assert username in gs_usernames
    gs_user_roles = gs_util.get_user_roles(username, auth)
    user_role = f"USER_{username.upper()}"
    assert user_role in gs_user_roles
    assert settings.LAYMAN_GS_ROLE in gs_user_roles
