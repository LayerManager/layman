from layman import LaymanError
import tests.asserts.final.publication as publication
import tests.asserts.processing as processing
import tests.asserts.processing.exception
import tests.asserts.processing.response
from test_tools import process_client
from .. import Action, Publication

LAYER_TYPE = process_client.LAYER_TYPE
MAP_TYPE = process_client.MAP_TYPE

KEY_ACTION = 'action'
KEY_CALL = 'call'
KEY_CALL_EXCEPTION = 'call_exception'
KEY_RESPONSE_ASSERTS = 'response_asserts'
KEY_EXCEPTION = 'exception'
KEY_EXCEPTION_ASSERTS = 'exception_asserts'
KEY_FINAL_ASSERTS = 'final_asserts'

COMMON_WORKSPACE = 'dynamic_test_workspace'

PUBLICATIONS = {
    Publication(COMMON_WORKSPACE, LAYER_TYPE, 'basic_sld'): [
        {
            KEY_ACTION: {
                KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': ['sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif'],
                    'style_file': 'sample/style/ne_10m_admin_0_countries.qml',
                }),
                KEY_CALL_EXCEPTION: {
                    KEY_EXCEPTION: LaymanError,
                    KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {'expected': {'http_code': 400,
                                                                                      'code': 48,
                                                                                      'message': 'Wrong combination of parameters',
                                                                                      'detail': 'Raster layers are not allowed to have QML style.',
                                                                                      }, }, ),
                    ],
                },
            },
            KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        },
        {
            KEY_ACTION: {
                KEY_CALL: Action(process_client.publish_workspace_publication, dict()),
                KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.same_infos, {'expected': {'name': 'basic_sld',
                                                                         'url': 'http://enjoychallenge.tech/rest/workspaces/dynamic_test_workspace/layers/basic_sld', }}),
                ],
            },
            KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    'exp_publication_detail': {'title': 'basic_sld',
                                               'style_type': 'sld',
                                               'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.854206196,
                                                                6269876.33561699],
                                               'access_rights': {'read': ['EVERYONE'], 'write': ['EVERYONE']},
                                               'file': {'path': 'layers/basic_sld/input_file/basic_sld.geojson', 'file_type': 'vector'},
                                               '_file': {
                                                   'path': '/layman_data_test/workspaces/dynamic_test_workspace/layers/basic_sld/input_file/basic_sld.geojson'},
                                               'description': None,
                                               'wfs': {'url': 'http://localhost:8000/geoserver/dynamic_test_workspace/wfs'},
                                               'style': {'type': 'sld'},
                                               'metadata': {'csw_url': 'http://localhost:3080/csw', }
                                               }
                }),
            ],
        },
        {
            KEY_ACTION: {
                KEY_CALL: Action(process_client.patch_workspace_publication, {
                    'file_paths': ['sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif'],
                    'style_file': 'sample/style/ne_10m_admin_0_countries.qml',
                }),
                KEY_CALL_EXCEPTION: {
                    KEY_EXCEPTION: LaymanError,
                    KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {'expected': {'http_code': 400,
                                                                                      'code': 48,
                                                                                      'message': 'Wrong combination of parameters',
                                                                                      'detail': 'Raster layers are not allowed to have QML style.',
                                                                                      }, }, ),
                    ],
                },
            },
            KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    'exp_publication_detail': {'title': 'basic_sld',
                                               'style_type': 'sld',
                                               'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.854206196,
                                                                6269876.33561699],
                                               'access_rights': {'read': ['EVERYONE'], 'write': ['EVERYONE']},
                                               'file': {'path': 'layers/basic_sld/input_file/basic_sld.geojson', 'file_type': 'vector'},
                                               '_file': {
                                                   'path': '/layman_data_test/workspaces/dynamic_test_workspace/layers/basic_sld/input_file/basic_sld.geojson'},
                                               'description': None,
                                               'wfs': {'url': 'http://localhost:8000/geoserver/dynamic_test_workspace/wfs'},
                                               'style': {'type': 'sld'},
                                               'metadata': {'csw_url': 'http://localhost:3080/csw', }
                                               }
                }),
            ],
        },
    ],
}
