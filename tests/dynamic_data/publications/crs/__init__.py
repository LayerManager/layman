import os
import copy

import tests.asserts.processing as processing
import tests.asserts.final.publication as publication
from test_tools import process_client
from . import vectors
from .. import util, common_layers as layers
from .... import Action, Publication, dynamic_data as consts

KEY_ACTION_PARAMS = 'action_params'
KEY_FILE_NAME = 'file_suffix'
KEY_INFO_VALUES = 'info_values'
KEY_THUMBNAIL = 'thumbnail'

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

REST_PARAMETRIZATION = {
    'with_chunks': {False: 'sync', True: 'chunks'},
    'compress': {False: '', True: 'zipped'},
}

TESTCASES = {
    'epsg_4326_shp': {
        KEY_FILE_NAME: 'small_layer_4326',
        KEY_INFO_VALUES: {**layers.SMALL_LAYER.info_values,
                          'file_extension': 'shp', },
        KEY_THUMBNAIL: layers.SMALL_LAYER.thumbnail,
    },
    'epsg_4326_ne': {
        KEY_FILE_NAME: 'small_layer_4326_ne',
        KEY_INFO_VALUES: {**layers.SMALL_LAYER.info_values,
                          'file_extension': 'shp', },
        KEY_THUMBNAIL: layers.SMALL_LAYER.thumbnail,
    },
}


def generate_local(workspace=None):
    workspace = workspace or consts.COMMON_WORKSPACE

    result = dict()
    for testcase, tc_params in TESTCASES.items():
        file_name = tc_params.get(KEY_FILE_NAME)
        file_paths = {'file_paths': [f'{DIRECTORY}/{file_name}.{ext}' for ext in ['shp', 'dbf', 'prj', 'shx', 'cpg', 'qmd']
                                     if os.path.exists(f'{DIRECTORY}/{file_name}.{ext}')]} if file_name else dict()
        action_params = {**file_paths,
                         **tc_params.get(KEY_ACTION_PARAMS, dict()),
                         }

        parametrization = {key: values for key, values in REST_PARAMETRIZATION.items()
                           if key not in action_params}
        rest_param_dicts = util.dictionary_product(parametrization)

        info_values = tc_params[KEY_INFO_VALUES]
        exp_thumbnail = tc_params[KEY_THUMBNAIL]

        for rest_param_dict in rest_param_dicts:
            test_case_postfix = '_'.join([REST_PARAMETRIZATION[key][value]
                                          for key, value in rest_param_dict.items()
                                          if REST_PARAMETRIZATION[key][value]])
            publ_name = "_".join([part for part in [testcase, 'post', test_case_postfix] if part])
            if any(k in rest_param_dict and rest_param_dict[k] != v for k, v in action_params.items()):
                continue

            post_info_values = copy.deepcopy(info_values)
            if rest_param_dict['compress']:
                post_info_values['gdal_prefix'] = '/vsizip/'
                post_info_values['file_extension'] = f'zip/{file_name}.shp'

            action_def = {
                consts.KEY_ACTION: {
                    consts.KEY_CALL: Action(process_client.publish_workspace_publication,
                                            {**action_params,
                                             **rest_param_dict}),
                    consts.KEY_RESPONSE_ASSERTS: [
                        Action(processing.response.valid_post, dict()),
                    ],
                },
                consts.KEY_FINAL_ASSERTS: [
                    *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                    Action(publication.internal.correct_values_in_detail, copy.deepcopy(post_info_values)),
                    Action(publication.internal.thumbnail_equals, {'exp_thumbnail': exp_thumbnail, }),
                    *tc_params.get(consts.KEY_FINAL_ASSERTS, list()),
                ]
            }
            result[Publication(workspace, process_client.LAYER_TYPE, publ_name)] = [action_def]

        for rest_param_dict in rest_param_dicts:
            test_case_postfix = '_'.join([REST_PARAMETRIZATION[key][value]
                                          for key, value in rest_param_dict.items()
                                          if REST_PARAMETRIZATION[key][value]])
            publ_name = "_".join([part for part in [testcase, 'patch', test_case_postfix] if part])
            patch_info_values = copy.deepcopy(info_values)
            if rest_param_dict['compress']:
                patch_info_values['gdal_prefix'] = '/vsizip/'
                patch_info_values['file_extension'] = f'zip/{file_name}.shp'

            patch_action = {
                consts.KEY_ACTION: {
                    consts.KEY_CALL: Action(process_client.patch_workspace_publication,
                                            {**action_params,
                                             **rest_param_dict}),
                    consts.KEY_RESPONSE_ASSERTS: [
                        Action(processing.response.valid_post, dict()),
                    ],
                },
                consts.KEY_FINAL_ASSERTS: [
                    *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                    Action(publication.internal.correct_values_in_detail, copy.deepcopy(patch_info_values)),
                    Action(publication.internal.thumbnail_equals, {'exp_thumbnail': exp_thumbnail, }),
                    *tc_params.get(consts.KEY_FINAL_ASSERTS, list()),
                ]
            }
            result[Publication(workspace, process_client.LAYER_TYPE, publ_name)] = [layers.DEFAULT_POST, patch_action]
    return result


def generate(workspace=None):
    return {
        **generate_local(workspace),
        **vectors.generate(workspace + '_vectors')
    }
