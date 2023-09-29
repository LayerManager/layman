import importlib
import pytest

from test_tools import util as test_util
from . import app, settings, LaymanError, util
from .util import XForwardedClass


@pytest.mark.parametrize('unsafe_input, exp_output', [
    ('Brno-město', 'brno_mesto'),
    ('Brno__město', 'brno_mesto'),
    (' ', ''),
    (' ?:"+  @', ''),
    ('01 Stanice vodních toků 26.4.2017 (voda)', '01_stanice_vodnich_toku_26_4_2017_voda'),
])
def test_slugify(unsafe_input, exp_output):
    assert util.slugify(unsafe_input) == exp_output


@pytest.mark.parametrize('workspace', settings.RESERVED_WORKSPACE_NAMES)
def test_check_reserved_workspace_names(workspace):
    with app.app_context():
        with pytest.raises(LaymanError) as exc_info:
            util.check_reserved_workspace_names(workspace)
        assert exc_info.value.code == 35
        assert exc_info.value.data['reserved_by'] == 'RESERVED_WORKSPACE_NAMES'


def assert_module_methods(module, methods):
    for method in methods:
        # print(f'test_module_methods: module={module.__name__}, method={method}')
        func = getattr(module, method, None)
        if func is None:
            raise Exception(
                f'Module {module.__name__} does not have {method} method.')


@pytest.mark.usefixtures('ensure_layman')
def test_publication_interface_methods():
    publication_source_methods = {
        'get_publication_uuid',
        'get_metadata_comparison',
        'pre_publication_action_check',
    }

    publication_provider_methods = {
        'get_usernames',
        'get_workspaces',
        'check_workspace_name',
        'ensure_whole_user',
        'delete_whole_user',
        'ensure_workspace',
        'delete_workspace',
    }

    provider_modules_getter = util.get_providers_from_source_names
    source_modules_getter = util.get_modules_from_names

    # In future, also parameters can be tested
    interfaces = [
        {
            'publication_type': 'layman.layer',
            'modules_getter': provider_modules_getter,
            'methods': publication_provider_methods,
        },
        {
            'publication_type': 'layman.map',
            'modules_getter': provider_modules_getter,
            'methods': publication_provider_methods,
        },
        {
            'publication_type': 'layman.layer',
            'modules_getter': source_modules_getter,
            'methods': publication_source_methods.union({
                'get_layer_info',
                'delete_layer',
                'patch_layer',
                'post_layer',
                'PATCH_MODE',
            }),
        },
        {
            'publication_type': 'layman.map',
            'modules_getter': source_modules_getter,
            'methods': publication_source_methods.union({
                'get_map_info',
                'patch_map',
                'post_map',
                'delete_map',
            }),
        },
    ]

    module_getters = [provider_modules_getter, source_modules_getter]
    for modules_getter in module_getters:
        assert set(settings.PUBLICATION_MODULES) == set(
            interface['publication_type'] for interface in interfaces
            if modules_getter == interface['modules_getter']
        )

    for interface in interfaces:
        publ_module = importlib.import_module(interface['publication_type'])
        type_def = publ_module.PUBLICATION_TYPES[interface['publication_type']]
        with app.app_context():
            modules = interface['modules_getter'](type_def['internal_sources'])
            methods = interface['methods']
            for module in modules:
                assert_module_methods(module, methods)


@pytest.mark.parametrize('endpoint, internal, params, expected_url', [
    ('rest_workspace_maps.get', False, {'workspace': 'workspace_name'},
     f'http://localhost:8000/rest/{settings.REST_WORKSPACES_PREFIX}/workspace_name/maps'),
    ('rest_workspace_layers.get', False, {'workspace': 'workspace_name'},
     f'http://localhost:8000/rest/{settings.REST_WORKSPACES_PREFIX}/workspace_name/layers'),
    ('rest_about.get_version', True, {}, 'http://layman_test_run_1:8000/rest/about/version'),
    ('rest_about.get_version', False, {}, 'http://localhost:8000/rest/about/version'),
])
def test_url_for(endpoint, internal, params, expected_url):
    with app.app_context():
        assert util.url_for(endpoint, internal=internal, **params) == expected_url


@pytest.mark.parametrize('endpoint, internal, x_forwarded_items, params, expected_url', [
    pytest.param('rest_workspace_maps.get', False, None, {'workspace': 'workspace_name'},
                 f'http://enjoychallenge.tech/rest/{settings.REST_WORKSPACES_PREFIX}/workspace_name/maps',
                 id='get-workspace-maps-external'),
    pytest.param('rest_about.get_version', True, None, {}, 'http://layman:8000/rest/about/version',
                 id='get-version-internal'),
    pytest.param('rest_about.get_version', False, None, {}, 'http://enjoychallenge.tech/rest/about/version',
                 id='get-version-external'),
    pytest.param('rest_workspace_layers.get', False, XForwardedClass(proto='https'), {'workspace': 'workspace_name'},
                 f'https://enjoychallenge.tech/rest/{settings.REST_WORKSPACES_PREFIX}/workspace_name/layers',
                 id='get-workspace-layers-x-forwarded-proto'),
    pytest.param('rest_workspace_layers.get', False, XForwardedClass(prefix='/proxy'), {'workspace': 'workspace_name'},
                 f'http://enjoychallenge.tech/proxy/rest/{settings.REST_WORKSPACES_PREFIX}/workspace_name/layers',
                 id='get-workspace-layers-x-forwarded-prefix'),
    pytest.param('rest_workspace_layers.get', False, XForwardedClass(prefix=''), {'workspace': 'workspace_name'},
                 f'http://enjoychallenge.tech/rest/{settings.REST_WORKSPACES_PREFIX}/workspace_name/layers',
                 id='get-workspace-layers-x-forwarded-prefix-empty-string'),
    pytest.param('rest_workspace_layers.get', False, XForwardedClass(proto='https', host='foo.com', prefix='/proxy'),
                 {'workspace': 'workspace_name'},
                 f'https://foo.com/proxy/rest/{settings.REST_WORKSPACES_PREFIX}/workspace_name/layers',
                 id='get-workspace-layers-x-forwarded-proto-host-prefix'),
    pytest.param('rest_workspace_layers.get', False, XForwardedClass(host='localhost:3001'),
                 {'workspace': 'workspace_name'},
                 f'http://localhost:3001/rest/{settings.REST_WORKSPACES_PREFIX}/workspace_name/layers',
                 id='get-workspace-layers-x-forwarded-host-port'),
])
def test__url_for(endpoint, internal, x_forwarded_items, params, expected_url):
    server_name = 'layman:8000'
    proxy_server_name = 'enjoychallenge.tech'
    with app.app_context():
        # pylint: disable=protected-access
        assert util._url_for(endpoint, server_name=server_name, proxy_server_name=proxy_server_name, internal=internal,
                             x_forwarded_items=x_forwarded_items, **params) == expected_url


@pytest.mark.parametrize('headers, exp_result', [
    pytest.param({'X-Forwarded-Prefix': '/layman-proxy'}, util.XForwardedClass(prefix='/layman-proxy'),
                 id='prefix_header'),
    pytest.param({
        'X-Forwarded-Proto': 'https',
        'X-Forwarded-Host': 'example.com',
        'X-Forwarded-Prefix': '/another-layman-proxy',
    }, util.XForwardedClass(proto='https', host='example.com', prefix='/another-layman-proxy'), id='three_headers'),
    pytest.param({
        'X-Forwarded-Host': 'localhost:3000',
    }, util.XForwardedClass(host='localhost:3000'), id='host_header_with_port'),
    pytest.param({
        'X-Forwarded-Proto': 'https',
        'X-Forwarded-Prefix': '/another-layman-proxy',
    }, util.XForwardedClass(proto='https', prefix='/another-layman-proxy'), id='proto_prefix_headers'),
    pytest.param({
        'X-Forwarded-Proto': 'https',
        'X-Forwarded-Host': 'example.com',
    }, util.XForwardedClass(proto='https', host='example.com'), id='proto_host_headers'),
    pytest.param({}, util.XForwardedClass(), id='without_header'),
])
def test_get_x_forwarded_items(headers, exp_result):
    result = util.get_x_forwarded_items(headers)
    assert result == exp_result


@pytest.mark.parametrize('headers, exp_error', [
    pytest.param(
        {'X-Forwarded-Prefix': 'layman-proxy'},
        {
            'http_code': 400,
            'code': 54,
            'data': {
                'header': 'X-Forwarded-Prefix',
                'message': 'Optional header X-Forwarded-Prefix is expected to be valid URL subpath starting with slash, or empty string.',
                'expected': 'Expected header matching regular expression ^(?:/[a-z0-9_-]+)*$',
                'found': 'layman-proxy',
            },
        }, id='prefix-without-slash'),
    pytest.param(
        {'X-Forwarded-Proto': ''},
        {
            'http_code': 400,
            'code': 54,
            'data': {
                'header': 'X-Forwarded-Proto',
                'message': 'Optional header X-Forwarded-Proto contains unsupported value.',
                'expected': "One of ['http', 'https']",
                'found': '',
            },
        }, id='empty-proto'),
    pytest.param(
        {'X-Forwarded-Proto': 'ftp'},
        {
            'http_code': 400,
            'code': 54,
            'data': {
                'header': 'X-Forwarded-Proto',
                'message': 'Optional header X-Forwarded-Proto contains unsupported value.',
                'expected': "One of ['http', 'https']",
                'found': 'ftp',
            },
        }, id='unsupported-proto'),
    pytest.param(
        {'X-Forwarded-Host': 'ABZ.COM'},
        {
            'http_code': 400,
            'code': 54,
            'data': {
                'header': 'X-Forwarded-Host',
                'message': 'Optional header X-Forwarded-Host contains unsupported value.',
                'expected': r'Expected header matching regular expression ^(?=.{1,253}\.?(?:\:[0-9]{1,5})?$)(?:(?!-)[a-z0-9-_]{1,63}(?<!-)(?:\.|(?:\:[0-9]{1,5})?$))+$',
                'found': 'ABZ.COM',
            },
        }, id='uppercase-host'),
    pytest.param(
        {'X-Forwarded-Host': ''},
        {
            'http_code': 400,
            'code': 54,
            'data': {
                'header': 'X-Forwarded-Host',
                'message': 'Optional header X-Forwarded-Host contains unsupported value.',
                'expected': r'Expected header matching regular expression ^(?=.{1,253}\.?(?:\:[0-9]{1,5})?$)(?:(?!-)[a-z0-9-_]{1,63}(?<!-)(?:\.|(?:\:[0-9]{1,5})?$))+$',
                'found': '',
            },
        }, id='empty-host'),
])
def test_get_x_forwarded_items_raises(headers, exp_error):
    with pytest.raises(LaymanError) as exc_info:
        util.get_x_forwarded_items(headers)
    test_util.assert_error(exp_error, exc_info)
