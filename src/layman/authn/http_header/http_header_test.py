from test_tools import process_client
import pytest
from layman import settings, app
from layman.common import prime_db_schema
from layman.http import LaymanError


@pytest.mark.usefixtures('ensure_layman')
def test_http_header():
    username = 'test_http_header_user'
    workspace = 'test_http_header_workspace'
    layername = 'test_http_header_layer'
    http_authn_headers = {
        settings.LAYMAN_AUTHN_HTTP_HEADER_NAME: username,
    }

    with pytest.raises(LaymanError) as exc_info:
        process_client.get_workspace_layer(workspace, layername, headers=http_authn_headers)
    assert exc_info.value.http_code == 403
    assert exc_info.value.code == 44
    assert exc_info.value.message == 'Unsuccessful HTTP Header authentication.'
    assert exc_info.value.data == 'Username test_http_header_user not recognized.'

    # reserve the username in prime DB schema
    with app.app_context():
        prime_db_schema.ensure_whole_user(
            username,
            {
                'issuer_id': 'test_http_header_issuer',
                'sub': username,
                'claims': {
                    'preferred_username': username,
                    'given_name': username,
                    'family_name': username,
                    'middle_name': username,
                    'name': username,
                    'email': f"{username}@example.com",
                }
            }
        )

    with pytest.raises(LaymanError) as exc_info:
        process_client.get_workspace_layer(workspace, layername, headers=http_authn_headers)
    assert exc_info.value.http_code == 404
    assert exc_info.value.code == 40
    assert exc_info.value.message == 'Workspace does not exist.'

    with app.app_context():
        prime_db_schema.delete_whole_user(username)
