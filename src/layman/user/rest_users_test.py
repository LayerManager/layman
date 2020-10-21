from layman import app, settings
from layman.util import url_for
from test import flask_client as client_util

client = client_util.client


def test_get_users(client):
    username = 'test_get_users_user'
    layername = 'test_get_users_layer'

    # Create username in layman
    client_util.publish_layer(username, layername, client)
    client_util.delete_layer(username, layername, client)

    with app.app_context():
        # users.GET
        url = url_for('rest_users.get')
        assert url.endswith('/' + settings.REST_USERS_PREFIX + '/')

        rv = client.get(url)
        assert rv.status_code == 200, rv.json
        assert username in [info["username"] for info in rv.json]
