import requests
import pytest

from layman import app, settings
from test_tools import process_client
from test_tools.util import url_for


@pytest.mark.usefixtures('ensure_layman')
def test_version():
    with app.app_context():
        r_url = url_for('rest_about.get_version')
    response = requests.get(r_url, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    process_client.raise_layman_error(response)
    result = response.json()
    assert 'about' in result.keys()
    assert 'applications' in result['about'].keys()
    assert 'layman' in result['about']['applications'].keys()
    assert 'version' in result['about']['applications']['layman'].keys()
    assert 'release-timestamp' in result['about']['applications']['layman'].keys()

    assert 'layman-test-client' in result['about']['applications'].keys()
    assert 'version' in result['about']['applications']['layman-test-client'].keys()

    assert 'data' in result['about'].keys()
    assert 'layman' in result['about']['data'].keys()
    assert 'last-migration' in result['about']['data']['layman'].keys()
    assert 'last-data-migration' in result['about']['data']['layman'].keys()
    assert 'last-schema-migration' in result['about']['data']['layman'].keys()
    assert result['about']['data']['layman']['last-migration'] == result['about']['data']['layman']['last-schema-migration']
