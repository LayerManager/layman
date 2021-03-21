import requests
import pytest

from layman import app, settings
from layman.util import url_for
from layman.common.prime_db_schema import ensure_whole_user


@pytest.mark.usefixtures('ensure_layman')
def test_get_users():
    username = 'test_get_users_user'
    userinfo = {"issuer_id": 'mock_test_rest_user_test',
                "sub": '1',
                "claims": {"email": "test@liferay.com",
                           "preferred_username": 'test_preferred',
                           "name": "test ensure user",
                           "given_name": "test",
                           "family_name": "user",
                           "middle_name": "ensure",
                           }
                }

    # Create username in layman
    with app.app_context():
        ensure_whole_user(username, userinfo)

        # users.GET
        url = url_for('rest_users.get')
        assert url.endswith('/' + settings.REST_USERS_PREFIX)

    rv = requests.get(url)
    assert rv.status_code == 200, rv.json()
    assert username in [info["username"] for info in rv.json()]
