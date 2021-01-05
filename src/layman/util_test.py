import pytest
import importlib

from . import app as app, settings, LaymanError, util
from .util import slugify, get_modules_from_names, get_providers_from_source_names
from test import process_client
from layman.layer import LAYER_TYPE


def test_slugify():
    assert slugify('Brno-město') == 'brno_mesto'
    assert slugify('Brno__město') == 'brno_mesto'
    assert slugify(' ') == ''
    assert slugify(' ?:"+  @') == ''
    assert slugify('01 Stanice vodních toků 26.4.2017 (voda)') == \
        '01_stanice_vodnich_toku_26_4_2017_voda'


def test_check_reserved_workspace_names():
    with app.app_context():
        for username in settings.RESERVED_WORKSPACE_NAMES:
            with pytest.raises(LaymanError) as exc_info:
                util.check_reserved_workspace_names(username)
            assert exc_info.value.code == 35
            assert exc_info.value.data['reserved_by'] == 'RESERVED_WORKSPACE_NAMES'


def assert_module_methods(module, methods):
    for method in methods:
        # print(f'test_module_methods: module={module.__name__}, method={method}')
        fn = getattr(module, method, None)
        if fn is None:
            raise Exception(
                f'Module {module.__name__} does not have {method} method.')


@pytest.mark.usefixtures('ensure_layman')
def test_publication_interface_methods():
    publication_source_methods = {
        'get_publication_uuid',
        'get_publication_infos',
        'get_metadata_comparison',
        'pre_publication_action_check',
    }

    publication_provider_methods = {
        'get_usernames',
        'check_username',
        'ensure_whole_user',
        'delete_whole_user',
    }

    provider_modules_getter = get_providers_from_source_names
    source_modules_getter = get_modules_from_names

    # In future, also parameters can be tested
    interfaces = [
        {
            'publication_type': 'layman.layer',
            'modules_getter': provider_modules_getter,
            'methods': publication_provider_methods.union({
                'check_new_layername',
            }),
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
                'get_layer_infos',
                'get_layer_info',
                'delete_layer',
                'patch_layer',
                'post_layer',
            }),
        },
        {
            'publication_type': 'layman.map',
            'modules_getter': source_modules_getter,
            'methods': publication_source_methods.union({
                'get_map_infos',
                'get_map_info',
                'patch_map',
                'post_map',
                'delete_map',
            }),
        },
    ]

    module_getters = [provider_modules_getter, source_modules_getter]
    for modules_getter in module_getters:
        assert set(settings.PUBLICATION_MODULES) == set([
            interface['publication_type'] for interface in interfaces
            if modules_getter == interface['modules_getter']
        ])

    for interface in interfaces:
        publ_module = importlib.import_module(interface['publication_type'])
        type_def = publ_module.PUBLICATION_TYPES[interface['publication_type']]
        with app.app_context():
            modules = interface['modules_getter'](type_def['internal_sources'])
            methods = interface['methods']
            for module in modules:
                assert_module_methods(module, methods)


class TestGetPublicationInfosClass:
    layer_both = 'test_get_publication_infos_layer_both'
    layer_read = 'test_get_publication_infos_layer_read'
    layer_none = 'test_get_publication_infos_layer_none'
    owner = 'test_get_publication_infos_user_owner'
    actor = 'test_get_publication_infos_user_actor'
    authz_headers_owner = process_client.get_authz_headers(owner)
    authz_headers_actor = process_client.get_authz_headers(actor)

    @pytest.fixture(scope="class")
    def provide_publications(self):
        username = self.owner
        authz_headers = self.authz_headers_owner
        layer_both = self.layer_both
        layer_read = self.layer_read
        layer_none = self.layer_none
        process_client.ensure_reserved_username(username, headers=authz_headers)
        process_client.publish_layer(username, layer_both, headers=authz_headers, access_rights={'read': 'EVERYONE', 'write': 'EVERYONE'})
        process_client.publish_layer(username, layer_read, headers=authz_headers, access_rights={'read': 'EVERYONE', 'write': username})
        process_client.publish_layer(username, layer_none, headers=authz_headers, access_rights={'read': username, 'write': username})
        yield
        process_client.delete_layer(username, layer_both, headers=authz_headers)
        process_client.delete_layer(username, layer_read, headers=authz_headers)
        process_client.delete_layer(username, layer_none, headers=authz_headers)

    @pytest.mark.parametrize('publ_type, context, expected_publications', [
        (LAYER_TYPE, {'actor_name': actor, 'access_type': 'read'}, {layer_both, layer_read},),
        (LAYER_TYPE, {'actor_name': actor, 'access_type': 'write'}, {layer_both},),
    ], )
    @pytest.mark.usefixtures('liferay_mock', 'ensure_layman', 'provide_publications')
    def test_get_publication_infos(self,
                                   publ_type,
                                   context,
                                   expected_publications):
        with app.app_context():
            infos = util.get_publication_infos(self.owner, publ_type, context)
        publ_set = set(infos.keys())
        assert publ_set == expected_publications, publ_set
