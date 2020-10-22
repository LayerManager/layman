import requests

from layman import app, settings
from layman.util import url_for
from test import process_client, process, flask_client as client_util

client = client_util.client


def test_get_users():
    username = 'test_get_users_user'
    layername = 'test_get_users_layer'

    proc = process.start_layman()

    # Create username in layman
    process_client.publish_layer(username, layername)
    process_client.delete_layer(username, layername)

    with app.app_context():
        # users.GET
        url = url_for('rest_users.get')
        assert url.endswith('/' + settings.REST_USERS_PREFIX)

        rv = requests.get(url)
        assert rv.status_code == 200, rv.json()
        assert username in [info["username"] for info in rv.json()]

    process.stop_process(proc)
