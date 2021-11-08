import tests.asserts.processing as processing
import tests.asserts.final.publication as publication
from test_tools import process_client
from . import util
from ... import Action, Publication, dynamic_data as consts

KEY_PUBLICATION_TYPE = 'publ_type'
KEY_ACTION_PARAMS = 'action_params'

REST_PARAMETRIZATION = {
    'with_chunks': {False: 'sync', True: 'chunks'},
    'compress': {False: '', True: 'zipped'},
}

TESTCASES = {
    'zip_and_other_than_main_file': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [
                'sample/style/small_layer.qml',
                'sample/layman.layer/small_layer.zip',
            ],
            'compress': False,
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
        parametrization = {key: values for key, values in REST_PARAMETRIZATION.items()
                           if key not in tc_params.get(KEY_ACTION_PARAMS, list())}
        rest_param_dicts = util.dictionary_product(parametrization)
        for rest_param_dict in rest_param_dicts:
            test_case_postfix = '_'.join([REST_PARAMETRIZATION[key][value]
                                          for key, value in rest_param_dict.items()
                                          if REST_PARAMETRIZATION[key][value]])
            if any(k in rest_param_dict and rest_param_dict[k] != v for k, v in tc_params[KEY_ACTION_PARAMS].items()):
                continue
            action_def = {
                consts.KEY_ACTION: {
                    consts.KEY_CALL: Action(process_client.publish_workspace_publication,
                                            {**tc_params[KEY_ACTION_PARAMS],
                                             **rest_param_dict}),
                    consts.KEY_RESPONSE_ASSERTS: [
                        Action(processing.response.valid_post, dict()),
                    ],
                },
                consts.KEY_FINAL_ASSERTS: [
                    *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                    *tc_params[consts.KEY_FINAL_ASSERTS],
                ]
            }
            publ_name = f"{testcase}_post_{test_case_postfix}"
            result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], publ_name)] = [action_def]

        patch = [
            {
                consts.KEY_ACTION: {
                    consts.KEY_CALL: Action(process_client.publish_workspace_publication,
                                            dict()),
                    consts.KEY_RESPONSE_ASSERTS: [
                        Action(processing.response.valid_post, dict()),
                    ],
                },
                consts.KEY_FINAL_ASSERTS: [
                    *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                ]
            },
        ]
        for rest_param_dict in rest_param_dicts:
            test_case_postfix = '_'.join([REST_PARAMETRIZATION[key][value]
                                          for key, value in rest_param_dict.items()
                                          if REST_PARAMETRIZATION[key][value]])
            action_def = {
                consts.KEY_ACTION: {
                    consts.KEY_CALL: Action(process_client.patch_workspace_publication,
                                            {**tc_params[KEY_ACTION_PARAMS],
                                             **rest_param_dict}),
                    consts.KEY_RESPONSE_ASSERTS: [
                        Action(processing.response.valid_post, dict()),
                    ],
                },
                consts.KEY_FINAL_ASSERTS: [
                    *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                    *tc_params[consts.KEY_FINAL_ASSERTS],
                ]
            }
            patch.append(action_def)
            publ_name = f"{testcase}_patch_{test_case_postfix}"
            result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], publ_name)] = patch
    return result
