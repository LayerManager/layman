    (COMMON_WORKSPACE, LAYER_TYPE, 'basic_sld'): [
        {'action': {'call': (process_client.ensure_publication, {'workspace': workspace,
                                                                 'publ_type': LAYER_TYPE,
                                                                 'layername': layername,
                                                                 'file_paths': [
                                                                     'sample/layman.map/internal_url_unauthorized_layer.json'],
                                                                 'access_rights': {'read': 'EVERYONE',
                                                                                   'write': f"{OWNER},{OWNER2}",
                                                                                   },
                                                                 'headers': HEADERS[OWNER],
                                                                 },),
                    'exception_asserts': {
                        (test_tools.assert_utils.assert_response_exception, {'http_code': 400,
                                                                             'code': 4,
                                                                             'message': 'Unsupported CRS of data file',
                                                                             'detail': {'found': 'None',
                                                                                        'supported_values': settings.INPUT_SRS_LIST},
                                                                             }),
                    },
                    'response_asserts': {
                        (test_tools.assert_utils.assert_response_bbox,
                         {'exp_bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699)}),
                    },
                    },
         'final_asserts': {(test_tools.assert_utils.assert_thumbnail, {'exp_thumbnail': 'test_tools/data/thumbnails/asdflůkasjd.png'}),
                           (test_tools.assert_util.assert_all_sources_bbox, {'expected_bbox': (14, 48, 16, 50)}),
                           (assert_everything, {
                               'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
                               'file_type': settings.FILE_TYPE_VECTOR,
                               'style_type': 'sld',
                               'async_error': {},
                           }),
                           (assert_visibility, {'exp_can_see': ['karel', 'pepa']}),
                           },
         },
    ]

Poznámky:
Asynchronní chyba pro nás není nijak specifická, testujeme ji assertovací metodou.
Smazaná publikace pro nás není nijak specifická, testujeme ji assertovací metodou.
Mezistavy můžeme kontrolovat pomocí jiné check_fn ve volání publish_workspace_publication.
Jedna metoda ověřuje hodnoty v get_publication_info, všechny ostatní testy věří hodnotám z get_publication_info.

Pravidla:
1. Každá položka v hodnotách PUBLICATIONS obsahuje 'action'
1. 'final_asserts' se pouštějí až když neběží žádný asynchronní krok (publikace je ve stavu COMPLETE nebo INCOMPLETE)


0. Krok
Připravit framework

1. Krok
[x] tests/static_data/single_publication/publications_test.py::test_get_publication_info_items[test_workspace-layman.layer-post_common_sld] PASSED
[x] tests/static_data/single_publication/publications_test.py::test_infos[test_workspace-layman.layer-post_common_sld] PASSED
tests/static_data/single_publication/publications_test.py::test_internal_info[test_workspace-layman.layer-post_common_sld] PASSED
tests/static_data/single_publication/publications_test.py::test_info[test_workspace-layman.layer-post_common_sld] PASSED
[x] tests/static_data/single_publication/publications_test.py::test_all_source_info[test_workspace-layman.layer-post_common_sld] PASSED
tests/static_data/single_publication/layers_test.py::test_geoserver_workspace[test_workspace-layman.layer-post_common_sld] PASSED

2. Krok
tests/static_data/single_publication/layers_test.py::test_info[test_workspace-layman.layer-post_common_sld] FAILED

3. Kroky
Přepisovat integrační testy ze src
Přepsat tests/failed_publications (staré zahodíme)
Kontrolovat odpovědi

tests/static_data/single_publication/layers_files_test.py::test_raster_files[workspace0-publ_type0-publication0] SKIPPED
tests/static_data/single_publication/layers_files_test.py::test_qml_files[workspace0-publ_type0-publication0] SKIPPED
tests/static_data/single_publication/layers_test.py::test_get_layer_style[test_workspace-layman.layer-post_common_sld] FAILED
tests/static_data/single_publication/layers_test.py::test_wms_layer[test_workspace-layman.layer-post_common_sld] FAILED
tests/static_data/single_publication/layers_test.py::test_fill_project_template[workspace0-publ_type0-publication0] SKIPPED
tests/static_data/single_publication/layers_test.py::test_gs_data_security[test_workspace-layman.layer-post_common_sld] PASSED
tests/static_data/single_publication/layers_test.py::test_micka_xml[workspace0-publ_type0-publication0] SKIPPED
tests/static_data/single_publication/layers_test.py::test_layer_attributes_in_db[workspace0-publ_type0-publication0] SKIPPED
tests/static_data/single_publication/maps_test.py::test_map_with_unauthorized_layer[workspace0-publ_type0-publication0] SKIPPED
tests/static_data/single_publication/patch_error_test.py::test_patch_raster_qml[workspace0-publ_type0-publication0] SKIPPED
tests/static_data/single_publication/patch_error_test.py::test_patch_qml_raster[workspace0-publ_type0-publication0] SKIPPED
tests/static_data/single_publication/publications_test.py::test_thumbnail[test_workspace-layman.layer-post_common_sld] PASSED
tests/static_data/single_publication/publications_test.py::test_auth_get_publications[test_workspace-layman.layer-post_common_sld] PASSED
tests/static_data/single_publication/publications_test.py::test_auth_get_publication[test_workspace-layman.layer-post_common_sld] PASSED
