import pytest
import importlib

from . import app as app, settings, LaymanError, util
from .util import slugify, get_modules_from_names, get_providers_from_source_names, url_for
from test import process_client
from layman import util as layman_util
from layman.layer import LAYER_TYPE
from layman.common.filesystem import uuid


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


@pytest.mark.usefixtures('ensure_layman', 'liferay_mock')
def test_get_users_workspaces():
    public_workspace = 'test_get_users_workspaces_workspace'
    user = 'test_get_users_workspaces_user'
    publication = 'test_get_users_workspaces_publication'
    authz_headers = process_client.get_authz_headers(user)

    process_client.ensure_reserved_username(user, authz_headers)

    for publication_type in process_client.PUBLICATION_TYPES:
        process_client.publish_publication(publication_type,
                                           public_workspace,
                                           publication)
        all_sources = []
        for type_def in util.get_publication_types(use_cache=False).values():
            all_sources += type_def['internal_sources']
        providers = get_providers_from_source_names(all_sources)
        for provider in providers:
            with app.app_context():
                usernames = provider.get_usernames()

            assert public_workspace not in usernames, (publication_type, provider)

        with app.app_context():
            usernames = util.get_usernames(use_cache=False)
            workspaces = util.get_workspaces(use_cache=False)

        assert user in usernames
        assert public_workspace not in usernames
        assert user in workspaces
        assert public_workspace in workspaces

        process_client.delete_publication(publication_type,
                                          public_workspace,
                                          publication)


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
        'get_metadata_comparison',
        'pre_publication_action_check',
    }

    publication_provider_methods = {
        'get_usernames',
        'get_workspaces',
        'check_username',
        'ensure_whole_user',
        'delete_whole_user',
        'ensure_workspace',
        'delete_workspace',
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
        publ_set = set([publication_name for (workspace, publication_type, publication_name) in infos.keys()])
        assert publ_set == expected_publications, publ_set


@pytest.mark.parametrize('publication_type', process_client.PUBLICATION_TYPES)
@pytest.mark.usefixtures('ensure_layman')
def test_get_publication_info_items(publication_type):
    workspace = 'test_get_publication_info_items_workspace'
    publication = 'test_get_publication_info_items_publication'

    process_client.publish_publication(publication_type, workspace, publication)

    with app.app_context():
        for source, source_def in layman_util.get_publication_types()[publication_type]['internal_sources'].items():
            for key in source_def.info_items:
                context = {'keys': [key]}
                info = layman_util.get_publication_info(workspace, publication_type, publication, context)
                assert key in info, info

    process_client.delete_publication(publication_type, workspace, publication)


@pytest.mark.parametrize('publication_type', process_client.PUBLICATION_TYPES)
@pytest.mark.usefixtures('ensure_layman')
def test_get_publication_infos(publication_type):
    workspace = 'test_get_publication_infos_user'
    publication = 'test_get_publication_infos_publication'
    title = "Test get publication infos - publication íářžý"

    process_client.publish_publication(publication_type, workspace, publication, title=title)

    with app.app_context():
        expected_result = {(workspace, publication_type, publication): {'name': publication,
                                                                        'title': title,
                                                                        'style_type': 'sld' if publication_type == LAYER_TYPE else None,
                                                                        'uuid': uuid.get_publication_uuid(publication_type,
                                                                                                          workspace,
                                                                                                          publication_type,
                                                                                                          publication),
                                                                        'type': publication_type,
                                                                        'access_rights': {'read': [settings.RIGHTS_EVERYONE_ROLE, ],
                                                                                          'write': [settings.RIGHTS_EVERYONE_ROLE, ],
                                                                                          }
                                                                        }}
        # util
        publication_infos = layman_util.get_publication_infos(workspace, publication_type)
        for publication_name in publication_infos:
            if publication_infos[publication_name].get('id'):
                del publication_infos[publication_name]['id']
        assert publication_infos == expected_result, (publication_infos, expected_result)

    process_client.delete_publication(publication_type, workspace, publication)


@pytest.mark.parametrize('endpoint, params, expected_url', [
    ('rest_workspace_maps.get', {'username': 'workspace_name'},
     f'http://{settings.LAYMAN_SERVER_NAME}/rest/{settings.REST_WORKSPACES_PREFIX}/workspace_name/maps'),
    ('rest_workspace_layers.get', {'username': 'workspace_name'},
     f'http://{settings.LAYMAN_SERVER_NAME}/rest/{settings.REST_WORKSPACES_PREFIX}/workspace_name/layers'),
])
def test_url_for(endpoint, params, expected_url):
    with app.app_context():
        assert url_for(endpoint, **params) == expected_url
