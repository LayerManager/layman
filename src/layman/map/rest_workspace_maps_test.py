import sys
import requests
import pytest

del sys.modules['layman']
from layman import app, settings
from test_tools import process_client
from test_tools.util import url_for


@pytest.mark.usefixtures('ensure_layman')
def test_get_map_title():
    workspace = 'test_get_map_title_user'
    maps = [("c_test_get_map_title_map", "C Test get map title - map title íářžý"),
            ("a_test_get_map_title_map", "A Test get map title - map title íářžý"),
            ("b_test_get_map_title_map", "B Test get map title - map title íářžý")
            ]
    sorted_maps = sorted(maps)

    for (name, title) in maps:
        process_client.publish_workspace_map(workspace, name, title=title)

    with app.app_context():
        url_get = url_for('rest_workspace_maps.get', workspace=workspace)
    # maps.GET
    response = requests.get(url_get, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    assert response.status_code == 200, response.json()

    for i in range(0, len(sorted_maps) - 1):
        assert response.json()[i]["name"] == sorted_maps[i][0]
        assert response.json()[i]["title"] == sorted_maps[i][1]

    for (name, title) in maps:
        process_client.delete_workspace_map(workspace, name)
