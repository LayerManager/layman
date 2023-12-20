import requests
import pytest

from layman import app, settings
from test_tools import role_service
from test_tools.util import url_for


@pytest.mark.usefixtures('ensure_layman')
def test_get_roles():
    rolename = 'TEST_GET_ROLES_ROLE'

    with app.app_context():
        # roles.GET
        url = url_for('rest_roles.get')
        assert url.endswith('/' + settings.REST_ROLES_PREFIX)

    # Without role
    response = requests.get(url, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    assert response.status_code == 200, response.json()
    assert response.json() == [settings.RIGHTS_EVERYONE_ROLE]

    # With role
    with app.app_context():
        role_service.ensure_role(rolename)
    response = requests.get(url, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    assert response.status_code == 200, response.json()
    assert response.json() == [rolename, settings.RIGHTS_EVERYONE_ROLE]

    role_service.delete_role(rolename)
