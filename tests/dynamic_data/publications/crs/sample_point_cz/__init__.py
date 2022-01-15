import os
import copy

from tests.asserts import util as asserts_util
import tests.asserts.processing as processing
import tests.asserts.final.publication as publication
from test_tools import process_client
from ... import util, common_layers as layers
from ..... import Action, Publication, dynamic_data as consts

KEY_ACTION_PARAMS = 'action_params'
KEY_FILE_NAME = 'file_suffix'
KEY_INFO_VALUES = 'info_values'
KEY_THUMBNAIL = 'thumbnail'

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

REST_PARAMETRIZATION = {
    'with_chunks': {False: 'sync', True: 'chunks'},
    'compress': {False: '', True: 'zipped'},
    'style_file': {f'{DIRECTORY}/sample_point_cz.sld': 'sld', f'{DIRECTORY}/sample_point_cz.qml': 'qml'}
}

SOURCE_EPSG_CODES = {
    4326: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [16.6066275955110711, 49.1989353676069285, 16.6068125589999127, 49.1990477233154735],
            }
        },
    },
}


def generate(workspace=None):
    workspace = workspace or consts.COMMON_WORKSPACE

    result = dict()
    def_publ_info_values = {
        'exp_publication_detail': {
            'bounding_box': [1848641.3277258177, 6308684.223766193, 1848661.9177672109, 6308703.364768417],
            'native_bounding_box': None,
        },
        'file_extension': 'shp',
        'publ_type_detail': ('vector', 'sld'),
    }

    for epsg_code, tc_params in SOURCE_EPSG_CODES.items():
        action_params = {
            'file_paths': [f'{DIRECTORY}/sample_point_cz_{epsg_code}.{ext}' for ext in ['shp', 'dbf', 'prj', 'shx', 'cpg', 'qmd']
                           if os.path.exists(f'{DIRECTORY}/sample_point_cz_{epsg_code}.{ext}')]
        }

        parametrization = {key: values for key, values in REST_PARAMETRIZATION.items()
                           if key not in action_params}
        rest_param_dicts = util.dictionary_product(parametrization)

        def_info_values = copy.deepcopy(def_publ_info_values)
        def_info_values['exp_publication_detail']['native_crs'] = f'EPSG:{epsg_code}'
        asserts_util.recursive_dict_update(def_info_values, tc_params.get(KEY_INFO_VALUES, dict()))

        exp_thumbnail = f'{DIRECTORY}/sample_point_cz_{epsg_code}_thumbnail.png'

        for rest_param_dict in rest_param_dicts:
            test_case_postfix = '_'.join([REST_PARAMETRIZATION[key][value]
                                          for key, value in rest_param_dict.items()
                                          if REST_PARAMETRIZATION[key][value]])
            publ_name = "_".join([part for part in ['points', f'{epsg_code}', 'post', test_case_postfix] if part])
            if any(k in rest_param_dict and rest_param_dict[k] != v for k, v in action_params.items()):
                continue

            post_info_values = copy.deepcopy(def_info_values)
            post_info_values['exp_publication_detail']['native_crs'] = f'EPSG:{epsg_code}'
            if rest_param_dict.get('compress'):
                post_info_values['gdal_prefix'] = '/vsizip/'
                post_info_values['file_extension'] = f'zip/sample_point_cz_{epsg_code}.shp'
            if rest_param_dict.get('style_file'):
                post_info_values['publ_type_detail'] = ('vector', REST_PARAMETRIZATION['style_file'][rest_param_dict['style_file']])

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
            publ_name = "_".join([part for part in ['points', f'{epsg_code}', 'patch', test_case_postfix] if part])
            patch_info_values = copy.deepcopy(def_info_values)
            patch_info_values['exp_publication_detail']['native_crs'] = f'EPSG:{epsg_code}'
            if rest_param_dict.get('compress'):
                patch_info_values['gdal_prefix'] = '/vsizip/'
                patch_info_values['file_extension'] = f'zip/sample_point_cz_{epsg_code}.shp'
            if rest_param_dict.get('style_file'):
                patch_info_values['publ_type_detail'] = ('vector', REST_PARAMETRIZATION['style_file'][rest_param_dict['style_file']])

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
