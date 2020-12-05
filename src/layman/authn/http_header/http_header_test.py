import pytest
from test import process, process_client
from layman import settings, app
from layman.common import prime_db_schema


ensure_layman = process.ensure_layman


@pytest.mark.usefixtures('ensure_layman')
def test_http_header():
    username = 'test_http_header_user'
    workspace = 'test_http_header_workspace'
    layername = 'test_http_header_layer'
    http_authn_headers = {
        settings.LAYMAN_AUTHN_HTTP_HEADER_NAME: username,
    }

    resp = process_client.get_layer(workspace, layername, headers=http_authn_headers, assert_status=False)
    assert resp.status_code == 403
    assert resp.json()['code'] == 44  # username not recognized by HTTP Header authentication

    # reserve the username in prime DB schema
    with app.app_context():
        prime_db_schema.ensure_whole_user(
            username,
            {
                'iss_id': 'test_http_header_issuer',
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

    resp = process_client.get_layer(workspace, layername, headers=http_authn_headers, assert_status=False)
    assert resp.status_code == 404
    assert resp.json()['code'] == 40  # username was recognized and authenticated, but workspace was not found

    with app.app_context():
        prime_db_schema.delete_whole_user(username)
