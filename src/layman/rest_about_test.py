import pytest
import requests

from layman import app
from layman.util import url_for
from test import process_client


@pytest.mark.usefixtures('ensure_layman')
def test_version():
    with app.app_context():
        r_url = url_for('rest_about.get_version')
    r = requests.get(r_url)
    process_client.raise_layman_error(r)
    result = r.json()
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
