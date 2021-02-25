import pytest
from layman import app
from .rest import parse_request_path


@pytest.mark.parametrize('request_path', [
    '/rest/workspaces/layers',
    '/rest/workspaces/layers/abc',
    '/rest/workspaces/username/abc',
    '/rest/workspaces/username/publications',
    '/rest/workspaces/username/publications/blablabla',
    '/rest/workspaces/username/publications/blablabla/da',
    '/rest/workspaces/users/layers',
    '/rest/workspaces/users/maps/map',
])
def test_parse_wrong_request_path(request_path):
    with app.app_context():
        assert parse_request_path(request_path) == (None, None, None), request_path


@pytest.mark.parametrize('request_path, exp_result', [
    ('/rest/workspaces/user_a/layers', ('user_a', 'layman.layer', None)),
    ('/rest/workspaces/user_a/layers/', ('user_a', 'layman.layer', None)),
    ('/rest/workspaces/user_a/maps/', ('user_a', 'layman.map', None)),
    ('/rest/workspaces/user_a/layers/abc', ('user_a', 'layman.layer', 'abc')),
    ('/rest/workspaces/user_a/layers/some_layer/some/nested/endpoint', ('user_a', 'layman.layer', 'some_layer')),
    ('/rest/workspaces/user_a/maps/a_map', ('user_a', 'layman.map', 'a_map')),
])
def test_parse_request_path(request_path, exp_result):
    with app.app_context():
        assert parse_request_path(request_path) == exp_result, request_path
