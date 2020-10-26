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


def test_source_methods():
    processes = process.start_layman()
    # In future, also parameters can be tested
    methods_to_call = {
        'layman.layer': {
            get_modules_from_names: {
                         'get_layer_infos',
                         'get_publication_uuid',
                         'get_layer_info',
                         'delete_layer',
                         'patch_layer',
                         'post_layer',
                         'get_publication_infos',
                         'get_metadata_comparison',
                         },
            get_providers_from_source_names: {
                         'get_usernames',
                         'check_username',
                         'ensure_whole_user',
                         'delete_whole_user',
                         'check_new_layername',
                         },
        },
        'layman.map': {
            get_modules_from_names: {
                'get_map_infos',
                'get_publication_uuid',
                'get_map_info',
                'patch_map',
                'post_map',
                'delete_map',
                'get_metadata_comparison',
            },
            get_providers_from_source_names: {
                'get_usernames',
                'check_username',
                'ensure_whole_user',
                'delete_whole_user',
            },
        },
    }

    assert set(settings.PUBLICATION_MODULES) == methods_to_call.keys()

    for publ_module in get_modules_from_names(settings.PUBLICATION_MODULES):
        for type_def in publ_module.PUBLICATION_TYPES.values():
            with app.app_context():
                publ_type_name = type_def['type']
                for modules_type, methods in methods_to_call[publ_type_name].items():
                    sources = modules_type(type_def['internal_sources'])
                    for module in sources:
                        for method in methods:
                            # print(f'test_source_methods: module={module}, method={method}')
                            fn = getattr(module, method, None)
                            if fn is None:
                                raise Exception(
                                    f'Module {module.__name__} does not have {method} method.')

    process.stop_process(processes)
