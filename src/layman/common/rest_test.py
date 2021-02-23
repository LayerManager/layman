import pytest
from layman import app
from .rest import parse_request_path


@pytest.mark.parametrize('request_path', [
    '/rest/layers',
    '/rest/layers/abc',
    '/rest/username/abc',
    '/rest/username/publications',
    '/rest/username/publications/blablabla',
    '/rest/username/publications/blablabla/da',
    '/rest/users/layers',
    '/rest/users/maps/map',
])
def test_parse_wrong_request_path(request_path):
    with app.app_context():
        assert parse_request_path(request_path) == (None, None, None), request_path


@pytest.mark.parametrize('request_path, exp_result', [
    ('/rest/user_a/layers', ('user_a', 'layman.layer', None)),
    ('/rest/user_a/layers/', ('user_a', 'layman.layer', None)),
    ('/rest/user_a/maps/', ('user_a', 'layman.map', None)),
    ('/rest/user_a/layers/abc', ('user_a', 'layman.layer', 'abc')),
    ('/rest/user_a/layers/some_layer/some/nested/endpoint', ('user_a', 'layman.layer', 'some_layer')),
    ('/rest/user_a/maps/a_map', ('user_a', 'layman.map', 'a_map')),
])
def test_parse_request_path(request_path, exp_result):
    with app.app_context():
        assert parse_request_path(request_path) == exp_result, request_path
