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
1. 'final_asserts' se většinou pouštějí až když neběží žádný asynchronní krok (publikace je ve stavu COMPLETE nebo INCOMPLETE), záleží na check_fn

