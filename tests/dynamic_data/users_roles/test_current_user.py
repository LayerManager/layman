import pytest

from layman import LaymanError
from test_tools import process_client
from tests.asserts import processing


@pytest.mark.usefixtures('ensure_layman_module', 'oauth2_provider_mock')
def test_patch():
    user = 'test_patch_current_user_username'
    headers = process_client.get_authz_headers(user)

    process_client.reserve_username(user, headers)


@pytest.mark.usefixtures('ensure_layman_module')
@pytest.mark.parametrize('params, exp_exception', [
    pytest.param({
        'username': 'test_patch_current_user_username'
    }, {
        'http_code': 403,
        'code': 30,
        'message': 'Unauthorized access',
    }, id='unauthorized'),
])
def test_patch_current_user_raises(params, exp_exception):
    with pytest.raises(LaymanError) as exc_info:
        process_client.reserve_username(**params)
    processing.exception.response_exception(expected=exp_exception, thrown=exc_info)
