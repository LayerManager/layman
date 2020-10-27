from . import app as app, settings
from .util import slugify, get_modules_from_names, get_providers_from_source_names
from test import process


def test_slugify():
    assert slugify('Brno-město') == 'brno_mesto'
    assert slugify('Brno__město') == 'brno_mesto'
    assert slugify(' ') == ''
    assert slugify(' ?:"+  @') == ''
    assert slugify('01 Stanice vodních toků 26.4.2017 (voda)') == \
           '01_stanice_vodnich_toku_26_4_2017_voda'


def assert_module_methods(module, methods):
    for method in methods:
        # print(f'test_module_methods: module={module.__name__}, method={method}')
        fn = getattr(module, method, None)
        if fn is None:
            raise Exception(
                f'Module {module.__name__} does not have {method} method.')


def test_source_methods():
    processes = process.start_layman()

    publication_source_methods = {
        'get_publication_uuid',
        'get_publication_infos',
        'get_metadata_comparison',
    }

    publication_provider_methods = {
        'get_usernames',
        'check_username',
        'ensure_whole_user',
        'delete_whole_user',
    }

    # In future, also parameters can be tested
    provider_methods_by_type = {
        'layman.layer': publication_provider_methods.union({
            'check_new_layername',
        }),
        'layman.map': publication_provider_methods,
    }

    source_methods_by_type = {
        'layman.layer': publication_source_methods.union({
            'get_layer_infos',
            'get_layer_info',
            'delete_layer',
            'patch_layer',
            'post_layer',
        }),
        'layman.map': publication_source_methods.union({
            'get_map_infos',
            'get_map_info',
            'patch_map',
            'post_map',
            'delete_map',
        }),
    }

    assert set(settings.PUBLICATION_MODULES) == provider_methods_by_type.keys()
    assert set(settings.PUBLICATION_MODULES) == source_methods_by_type.keys()

    for publ_module in get_modules_from_names(settings.PUBLICATION_MODULES):
        for type_def in publ_module.PUBLICATION_TYPES.values():
            with app.app_context():
                publ_type = type_def['type']

                provider_modules = get_providers_from_source_names(type_def['internal_sources'])
                provider_methods = provider_methods_by_type[publ_type]
                for provider_module in provider_modules:
                    assert_module_methods(provider_module, provider_methods)

                source_modules = get_modules_from_names(type_def['internal_sources'])
                source_methods = source_methods_by_type[publ_type]
                for source_module in source_modules:
                    assert_module_methods(source_module, source_methods)

    process.stop_process(processes)
