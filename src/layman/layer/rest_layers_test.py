import sys
import pytest
import requests

del sys.modules['layman']

from layman import app
from layman import util as layman_util
from test import process_client


@pytest.mark.usefixtures('ensure_layman')
def test_get_layer_title():
    username = 'test_get_layer_title_user'
    layers = [("c_test_get_layer_title_layer", "C Test get layer title - map layer íářžý"),
              ("a_test_get_layer_title_layer", "A Test get layer title - map layer íářžý"),
              ("b_test_get_layer_title_layer", "B Test get layer title - map layer íářžý")
              ]
    sorted_layers = sorted(layers)

    for (name, title) in layers:
        process_client.publish_layer(username, name, title=title)

    # layers.GET
    with app.app_context():
        url = layman_util.url_for('rest_layers.get', username=username)
    rv = requests.get(url)
    assert rv.status_code == 200, rv.text

    for i in range(0, len(sorted_layers) - 1):
        assert rv.json()[i]["name"] == sorted_layers[i][0]
        assert rv.json()[i]["title"] == sorted_layers[i][1]

    for (name, title) in layers:
        process_client.delete_layer(username, name)
