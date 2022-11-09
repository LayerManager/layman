import tests.asserts.processing as processing
import tests.asserts.final.publication as publication
from test_tools import process_client, util
from .. import common_publications as publications
from .... import Action, Publication, dynamic_data as consts

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
            Action(publication.internal.correct_values_in_detail, publications.SMALL_LAYER_ZIP.info_values),
            Action(publication.internal.thumbnail_equals, {
                'exp_thumbnail': publications.SMALL_LAYER_ZIP.thumbnail,
            }),
        ],
    },
    'capslock_extension_zip': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [
                'sample/layman.layer/smaLL_Layer.ZIP',
            ],
            'compress': False,
        },
        consts.KEY_FINAL_ASSERTS: [
            Action(publication.internal.correct_values_in_detail, publications.SMALL_LAYER_ZIP.info_values),
            Action(publication.internal.thumbnail_equals, {
                'exp_thumbnail': publications.SMALL_LAYER_ZIP.thumbnail,
            }),
        ],
    },
    'capslock_extension_geojson': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [
                'sample/layman.layer/SMAll_layER.GeOjSoN',
            ],
        },
        consts.KEY_FINAL_ASSERTS: [
            *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
            Action(publication.internal.thumbnail_equals, {
                'exp_thumbnail': publications.SMALL_LAYER.thumbnail,
            }),
        ],
    },
    'capslock_extension_json': {
        KEY_PUBLICATION_TYPE: process_client.MAP_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [
                'sample/layman.map/smaLL_Map.jSOn',
            ],
        },
        consts.KEY_FINAL_ASSERTS: [
        ],
    },
}


def generate(workspace=None):
    workspace = workspace or consts.COMMON_WORKSPACE

    result = dict()
    for testcase, tc_params in TESTCASES.items():
        parametrization = {key: values for key, values in REST_PARAMETRIZATION.items()
                           if key not in tc_params.get(KEY_ACTION_PARAMS, list())}
        rest_param_dicts = util.dictionary_product(parametrization) if tc_params[KEY_PUBLICATION_TYPE] == process_client.LAYER_TYPE\
            else [dict()]
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
                    *publication.IS_PUBLICATION_COMPLETE_AND_CONSISTENT[tc_params[KEY_PUBLICATION_TYPE]],
                    *tc_params[consts.KEY_FINAL_ASSERTS],
                ]
            }
            publ_name = "_".join([part for part in [testcase, 'post', test_case_postfix] if part])
            result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], publ_name)] = [action_def]

        for rest_param_dict in rest_param_dicts:
            test_case_postfix = '_'.join([REST_PARAMETRIZATION[key][value]
                                          for key, value in rest_param_dict.items()
                                          if REST_PARAMETRIZATION[key][value]])
            patch_action = {
                consts.KEY_ACTION: {
                    consts.KEY_CALL: Action(process_client.patch_workspace_publication,
                                            {**tc_params[KEY_ACTION_PARAMS],
                                             **rest_param_dict}),
                    consts.KEY_RESPONSE_ASSERTS: [
                        Action(processing.response.valid_post, dict()),
                    ],
                },
                consts.KEY_FINAL_ASSERTS: [
                    *publication.IS_PUBLICATION_COMPLETE_AND_CONSISTENT[tc_params[KEY_PUBLICATION_TYPE]],
                    *tc_params[consts.KEY_FINAL_ASSERTS],
                ]
            }
            publ_name = "_".join([part for part in [testcase, 'patch', test_case_postfix] if part])
            result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], publ_name)] = [
                publications.DEFAULT_POST_DICT[tc_params[KEY_PUBLICATION_TYPE]], patch_action]
    return result
