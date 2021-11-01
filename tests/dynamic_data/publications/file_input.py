import tests.asserts.processing as processing
import tests.asserts.final.publication as publication
from test_tools import process_client
from ... import Action, Publication, dynamic_data as consts

KEY_PUBLICATION_TYPE = 'publ_type'
KEY_ACTION_PARAMS = 'action_params'

TESTCASES = {
    'zip_and_other_than_main_file': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [
                'sample/style/small_layer.qml',
                'sample/layman.layer/small_layer.zip',
            ],
        },
        consts.KEY_FINAL_ASSERTS: [
            Action(publication.internal.correct_values_in_detail, {
                'exp_publication_detail': {
                    'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699],
                },
                'file_extension': 'zip/small_layer.geojson',
                'gdal_prefix': '/vsizip/',
                'publ_type_detail': ('vector', 'sld'),
            }),
            Action(publication.internal.thumbnail_equals, {
                'exp_thumbnail': 'sample/style/basic_sld.png',
            }),
        ],
    },
}


def generate(workspace=None):
    workspace = workspace or consts.COMMON_WORKSPACE

    result = dict()
    for testcase, tc_params in TESTCASES.items():
        post = [{
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication,
                                        tc_params[KEY_ACTION_PARAMS]),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ], },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                *tc_params[consts.KEY_FINAL_ASSERTS],
            ],
        }]
        post_chunks = [{
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication,
                                        {**tc_params[KEY_ACTION_PARAMS],
                                         'with_chunks': True, }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ], },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                *tc_params[consts.KEY_FINAL_ASSERTS],
            ],
        }]
        result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], testcase + '_post_sync')] = post
        result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], testcase + '_post_chunks')] = post_chunks

    return result
