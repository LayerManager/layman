import importlib
import pytest

from . import app, settings, LaymanError, util


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


@pytest.mark.parametrize('endpoint, internal, params, expected_url', [
    ('rest_workspace_maps.get', False, {'workspace': 'workspace_name'},
     f'http://enjoychallenge.tech/rest/{settings.REST_WORKSPACES_PREFIX}/workspace_name/maps'),
    ('rest_workspace_layers.get', False, {'workspace': 'workspace_name'},
     f'http://enjoychallenge.tech/rest/{settings.REST_WORKSPACES_PREFIX}/workspace_name/layers'),
    ('rest_about.get_version', True, {}, 'http://layman:8000/rest/about/version'),
    ('rest_about.get_version', False, {}, 'http://enjoychallenge.tech/rest/about/version'),
])
def test__url_for(endpoint, internal, params, expected_url):
    server_name = 'layman:8000'
    proxy_server_name = 'enjoychallenge.tech'
    with app.app_context():
        # pylint: disable=protected-access
        assert util._url_for(endpoint, server_name=server_name, proxy_server_name=proxy_server_name, internal=internal,
                             **params) == expected_url


@pytest.mark.parametrize('headers, exp_result', [
    pytest.param({'X-Forwarded-Prefix': '/layman-proxy'}, '/layman-proxy', id='simple_header'),
    pytest.param({}, None, id='without_header'),
])
def test_get_x_forwarded_prefix(headers, exp_result):
    result = util.get_x_forwarded_prefix(headers)
    assert result == exp_result
