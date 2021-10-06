import tests.asserts.final.publication as publication
import tests.asserts.processing as processing
from test_tools import process_client
from . import predefined_actions
from .. import Action, Publication, dynamic_data as consts


PUBLICATIONS = {
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'basic_sld'): [
        {
            consts.KEY_ACTION: predefined_actions.POST_TIF_WITH_QML,
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, dict()),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.same_infos, {'expected': {'name': 'basic_sld',
                                                                         'url': 'http://enjoychallenge.tech/rest/workspaces/dynamic_test_workspace/layers/basic_sld', }}),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
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
            consts.KEY_ACTION: predefined_actions.PATCH_TIF_WITH_QML,
            consts.KEY_FINAL_ASSERTS: [
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
