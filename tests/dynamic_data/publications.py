import tests.asserts.final.publication as publication
import tests.asserts.processing as processing
from test_tools import process_client
from . import predefined_actions, predefined_infos
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
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    'exp_publication_detail': predefined_infos.BASIC_SLD_LAYER
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'sample/style/basic_sld.png',
                }),
            ],
        },
        {
            consts.KEY_ACTION: predefined_actions.PATCH_TIF_WITH_QML,
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    'exp_publication_detail': predefined_infos.BASIC_SLD_LAYER
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'sample/style/basic_sld.png',
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_sld'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': ['sample/layman.layer/small_layer.zip'],
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    'exp_publication_detail': {
                        **predefined_infos.BASIC_SLD_LAYER,
                        '_file': {
                            'path': '/layman_data_test/workspaces/dynamic_test_workspace/layers/zipped_sld/input_file/zipped_sld.zip/small_layer.geojson'
                        },
                        'file': {
                            'path': 'layers/zipped_sld/input_file/zipped_sld.zip/small_layer.geojson'
                        },
                    },
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'sample/style/basic_sld.png',
                }),
            ],
        },
    ]
}
