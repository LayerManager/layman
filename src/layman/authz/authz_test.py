import pytest

from . import authorize, MULTI_PUBLICATION_PATH_PATTERN, SINGLE_PUBLICATION_PATH_PATTERN


def test_authorize_assert_wrong_path():
    wrong_paths = [
        '/rest/layers',
        '/rest/layers/abc',
        '/rest/username/abc',
        '/rest/username/publications',
        '/rest/username/publications/blablabla',
        '/rest/username/publications/blablabla/da',
        '/rest/users/layers',
        '/rest/users/maps/map',
    ]
    for wrong_path in wrong_paths:
        with pytest.raises(Exception) as exc_info:
            authorize(wrong_path, 'GET', None)
        assert str(exc_info.value) == f"Authorization module is unable to authorize path {wrong_path}"


def test_authorize_accepts_path():
    multi_paths = [
        '/rest/user_a/layers',
        '/rest/user_a/layers/',
        '/rest/user_a/maps/',
    ]
    for req_path in multi_paths:
        m = MULTI_PUBLICATION_PATH_PATTERN.match(req_path)
        assert m, {req_path}

    single_paths = [
        '/rest/user_a/layers/abc',
        '/rest/user_a/layers/some_layer/some/nested/endpoint',
        '/rest/user_a/maps/a_map',
    ]
    for req_path in single_paths:
        m = SINGLE_PUBLICATION_PATH_PATTERN.match(req_path)
        assert m, f"{req_path} {SINGLE_PUBLICATION_PATH_PATTERN}"
