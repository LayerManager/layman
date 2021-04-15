import pytest
from layman import app, settings, LaymanError
from . import get_publications_consts
from .rest import parse_request_path, get_integer_from_param


@pytest.mark.parametrize('request_path', [
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/layers',
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/layers/abc',
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/username/abc',
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/username/publications',
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/username/publications/blablabla',
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/username/publications/blablabla/da',
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/users/layers',
    f'/rest/{settings.REST_WORKSPACES_PREFIX}/users/maps/map',
    f'/rest/layers/abc',
    f'/rest/username/abc',
    f'/rest/username/publications',
    f'/rest/username/publications/blablabla',
    f'/rest/username/publications/blablabla/da',
    f'/rest/users/layers',
    f'/rest/users/maps/map',
])
def test_parse_wrong_request_path(request_path):
    with app.app_context():
        assert parse_request_path(request_path) == (None, None, None), request_path


@pytest.mark.parametrize('request_path, exp_result', [
    (f'/rest/{settings.REST_WORKSPACES_PREFIX}/user_a/layers', ('user_a', 'layman.layer', None)),
    (f'/rest/{settings.REST_WORKSPACES_PREFIX}/user_a/layers/', ('user_a', 'layman.layer', None)),
    (f'/rest/{settings.REST_WORKSPACES_PREFIX}/user_a/maps/', ('user_a', 'layman.map', None)),
    (f'/rest/{settings.REST_WORKSPACES_PREFIX}/user_a/layers/abc', ('user_a', 'layman.layer', 'abc')),
    (f'/rest/{settings.REST_WORKSPACES_PREFIX}/user_a/layers/some_layer/some/nested/endpoint', ('user_a', 'layman.layer', 'some_layer')),
    (f'/rest/{settings.REST_WORKSPACES_PREFIX}/user_a/maps/a_map', ('user_a', 'layman.map', 'a_map')),
    (f'/rest/user_a/layers', ('user_a', 'layman.layer', None)),
    (f'/rest/user_a/layers/', ('user_a', 'layman.layer', None)),
    (f'/rest/user_a/maps/', ('user_a', 'layman.map', None)),
    (f'/rest/user_a/layers/abc', ('user_a', 'layman.layer', 'abc')),
    (f'/rest/user_a/layers/some_layer/some/nested/endpoint', ('user_a', 'layman.layer', 'some_layer')),
    (f'/rest/user_a/maps/a_map', ('user_a', 'layman.map', 'a_map')),
    (f'/rest/layers', (None, 'layman.layer', None)),
    (f'/rest/maps', (None, 'layman.map', None)),
])
def test_parse_request_path(request_path, exp_result):
    with app.app_context():
        assert parse_request_path(request_path) == exp_result, request_path


@pytest.mark.parametrize('request_args, param_name, expected_value', [
    (dict(), 'integer', None),
    ({'integer': '8'}, 'integer', 8),
    ({'integer': '-8'}, 'integer', -8),
    ({'integer': '0'}, 'integer', 0),
    ({'integer': '+4'}, 'integer', 4),
])
def test_get_integer_from_param(request_args, param_name, expected_value):
    result = get_integer_from_param(request_args, param_name)
    assert result == expected_value


@pytest.mark.parametrize('request_args, param_name, other_params, expected_expected', [
    ({'integer': '0'}, 'integer', {'zero': False}, 'value <> 0'),
    ({'integer': '-44'}, 'integer', {'negative': False, 'zero': False}, 'value > 0'),
    ({'integer': '7'}, 'integer', {'positive': False}, 'value <= 0'),
    ({'integer': 'asfg'}, 'integer', {'zero': False}, {'text': 'Integer with optional sign',
                                                       'regular_expression': get_publications_consts.INTEGER_PATTERN}),
])
def test_get_integer_from_param_fail(request_args, param_name, other_params, expected_expected):
    with pytest.raises(LaymanError) as exc_info:
        get_integer_from_param(request_args, param_name, **other_params)
    assert exc_info.value.code == 2
    assert exc_info.value.http_code == 400
    assert exc_info.value.data['expected'] == expected_expected
