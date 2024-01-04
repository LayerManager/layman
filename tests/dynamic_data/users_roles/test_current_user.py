import pytest

from test_tools import process_client


@pytest.mark.usefixtures('ensure_layman_module', 'oauth2_provider_mock')
def test_patch():
    user = 'test_patch_current_user_username'
    headers = process_client.get_authz_headers(user)

    process_client.reserve_username(user, headers)
