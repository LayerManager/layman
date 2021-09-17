import os
import requests
import pytest

from layman import app
from test_tools import process_client
from test_tools.util import url_for


@pytest.mark.usefixtures('ensure_layman')
def test_get_style_info():
    style_file = 'test_tools/data/style/small_layer_external_circle.qml'
    with app.app_context():
        r_url = url_for('rest_tools.get_style_info')

    files = [('style', (os.path.basename(style_file), open(style_file, 'rb')))]

    response = requests.get(r_url,
                            files=files)
    process_client.raise_layman_error(response)

    expected_json = {'type': 'qml',
                     'external_files': ['./circle-15.svg', ]}

    assert response.json() == expected_json
