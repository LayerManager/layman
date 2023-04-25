import copy
import os
import logging

from layman import LaymanError, settings
from layman.layer.util import EXTERNAL_TABLE_URI_PATTERN
from tests.asserts import util as asserts_util
from tests.asserts import processing
from tests.asserts.final import publication
from test_tools import process_client, util
from .. import common_publications as publications
from .... import Action, Publication, dynamic_data as consts, EnumTestTypes, EnumTestKeys

KEY_PUBLICATION_TYPE = 'publ_type'
KEY_ACTION_PARAMS = 'action_params'
KEY_EXPECTED_EXCEPTION = 'expected_exception'
KEY_DEFAULT = 'default'
KEY_PATCHES = 'patches'
KEY_PATCH_POST = 'post_params'
KEY_SKIP_POST = 'skip_post'
KEY_ONLY_FIRST_PARAMETRIZATION = 'only_first_parametrization'
KEY_FAILED_INFO_KEY = 'failed_info_key'

DIRECTORY = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)

REST_PARAMETRIZATION = {
    'with_chunks': {False: '', True: 'chunks'},
    'compress': {False: '', True: 'zipped'},
}

TESTCASES = {
    'partial_external_table_uri': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_ACTION_PARAMS: {
            'external_table_uri': 'external_table_uri',
            'compress': False,
            'with_chunks': False,
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'message': 'Wrong parameter value',
                          'data': {'parameter': 'external_table_uri',
                                   'message': 'Parameter `external_table_uri` is expected to have URI scheme `postgresql`',
                                   'expected': EXTERNAL_TABLE_URI_PATTERN,
                                   'found': {
                                       'external_table_uri': 'external_table_uri',
                                       'uri_scheme': '',
                                   },
                                   },
                          },
        },
        KEY_PATCHES: {
            'full': {
                KEY_PATCH_POST: {},
            },
        },
    },
    'crs_and_external_table_uri': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_ACTION_PARAMS: {
            'crs': 'EPSG:4326',
            'external_table_uri': 'postgresql://username:password@host:port/dbname?table=table_name&geo_column=geo_column_name',
            'compress': False,
            'with_chunks': False,
            'skip_asserts': True,
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 48,
                          'message': 'Wrong combination of parameters',
                          'data': {
                              'parameters': ['crs', 'file'],
                              'message': 'Parameter `crs` needs also parameter `file`.',
                              'expected': 'Input files in `file` parameter or empty `crs` parameter.',
                              'found': {
                                  'crs': 'EPSG:4326',
                                  'file': [],
                              }},
                          },
        },
        KEY_PATCHES: {
            'full': {
                KEY_PATCH_POST: {},
            },
        },
    },
}

VALIDATION_PATCH_ACTION = {
    consts.KEY_ACTION: {
        consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
            'file_paths': ['sample/layman.layer/small_layer.geojson'],
            'style_file': 'sample/style/basic.sld',
        }),
        consts.KEY_RESPONSE_ASSERTS: [
            Action(processing.response.valid_post, {}),
        ],
    },
    consts.KEY_FINAL_ASSERTS: [
        *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
        Action(publication.internal.correct_values_in_detail, publications.SMALL_LAYER.info_values),
        Action(publication.internal.thumbnail_equals, {
            'exp_thumbnail': publications.SMALL_LAYER.thumbnail,
        }),
    ],
}


def generate(workspace=None):
    workspace = workspace or consts.COMMON_WORKSPACE
    test_type_str = os.getenv(EnumTestKeys.TYPE.value) or EnumTestTypes.MANDATORY.value
    test_type = EnumTestTypes(test_type_str)
    default_only_first_parametrization = test_type != EnumTestTypes.OPTIONAL

    result = {}
    for testcase, tc_params in TESTCASES.items():
        if test_type == EnumTestTypes.MANDATORY:
            if tc_params.get(EnumTestKeys.TYPE, EnumTestTypes.MANDATORY) == EnumTestTypes.OPTIONAL:
                continue

        failed_info_key = tc_params.get(KEY_FAILED_INFO_KEY, 'file')
        assert_no_bbox_and_crs = KEY_FAILED_INFO_KEY not in tc_params
        if not tc_params.get(KEY_SKIP_POST, False):
            action_parametrization = util.get_test_case_parametrization(param_parametrization=REST_PARAMETRIZATION,
                                                                        only_first_parametrization=default_only_first_parametrization,
                                                                        default_params=tc_params[KEY_ACTION_PARAMS],
                                                                        action_parametrization=[('', None, []), ],
                                                                        )
            for test_case_postfix, _, _, rest_param_dict in action_parametrization:
                rest_param_frozen_set = frozenset(rest_param_dict.items())
                default_exp_exception = copy.deepcopy(tc_params[KEY_EXPECTED_EXCEPTION][KEY_DEFAULT])
                exception_diff = tc_params[KEY_EXPECTED_EXCEPTION].get(rest_param_frozen_set, {})
                exp_exception = asserts_util.recursive_dict_update(default_exp_exception, copy.deepcopy(exception_diff))
                is_sync = exp_exception.pop('sync')
                if is_sync:
                    action_def = {
                        consts.KEY_ACTION: {
                            consts.KEY_CALL: Action(process_client.publish_workspace_publication,
                                                    {**tc_params[KEY_ACTION_PARAMS],
                                                     **rest_param_dict}),
                            consts.KEY_CALL_EXCEPTION: {
                                consts.KEY_EXCEPTION: LaymanError,
                                consts.KEY_EXCEPTION_ASSERTS: [
                                    Action(processing.exception.response_exception, {'expected': exp_exception}, ),
                                ],
                            }, },
                        consts.KEY_FINAL_ASSERTS: [
                            Action(publication.internal.does_not_exist, {})
                        ],
                    }
                    action_list = [action_def]
                else:
                    action_def = {
                        consts.KEY_ACTION: {
                            consts.KEY_CALL: Action(process_client.publish_workspace_publication,
                                                    {**tc_params[KEY_ACTION_PARAMS],
                                                     **rest_param_dict}),
                            consts.KEY_RESPONSE_ASSERTS: [
                                Action(processing.response.valid_post, {}),
                            ],
                        },
                        consts.KEY_FINAL_ASSERTS: [
                            Action(publication.rest.async_error_in_info_key, {'info_key': failed_info_key,
                                                                              'expected': exp_exception, }, ),
                        ],
                    }
                    if assert_no_bbox_and_crs:
                        action_def[consts.KEY_FINAL_ASSERTS].append(Action(publication.internal.no_bbox_and_crs, {}))
                    action_list = [action_def, VALIDATION_PATCH_ACTION]
                publ_name = f"{testcase}_post{test_case_postfix}"
                result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], publ_name)] = action_list

        for patch_key, patch_params in tc_params.get(KEY_PATCHES, {}).items():
            action_parametrization = util.get_test_case_parametrization(param_parametrization=REST_PARAMETRIZATION,
                                                                        only_first_parametrization=default_only_first_parametrization,
                                                                        default_params={**tc_params[KEY_ACTION_PARAMS],
                                                                                        **patch_params.get(KEY_ACTION_PARAMS, {})},
                                                                        action_parametrization=[('', None, []), ],
                                                                        )
            for test_case_postfix, _, _, rest_param_dict in action_parametrization:
                patch = [
                    {
                        consts.KEY_ACTION: {
                            consts.KEY_CALL: Action(process_client.publish_workspace_publication,
                                                    patch_params[KEY_PATCH_POST]),
                            consts.KEY_RESPONSE_ASSERTS: [
                                Action(processing.response.valid_post, {}),
                            ],
                        },
                        consts.KEY_FINAL_ASSERTS: [
                            *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                        ]
                    },
                ]
                rest_param_frozen_set = frozenset(rest_param_dict.items())
                default_exp_exception = copy.deepcopy(tc_params[KEY_EXPECTED_EXCEPTION][KEY_DEFAULT])
                exception_diff_post = tc_params[KEY_EXPECTED_EXCEPTION].get(rest_param_frozen_set, {})
                exception_diff_patch = patch_params.get(KEY_EXPECTED_EXCEPTION, {}).get(rest_param_frozen_set, {})
                exception_diff = asserts_util.recursive_dict_update(exception_diff_post, exception_diff_patch, keep_replace_key=True)
                exp_exception = asserts_util.recursive_dict_update(default_exp_exception, copy.deepcopy(exception_diff))
                is_sync = exp_exception.pop('sync')
                if is_sync:
                    action_def = {
                        consts.KEY_ACTION: {
                            consts.KEY_CALL: Action(process_client.patch_workspace_publication,
                                                    {**tc_params[KEY_ACTION_PARAMS],
                                                     **patch_params.get(KEY_ACTION_PARAMS, {}),
                                                     **rest_param_dict}),
                            consts.KEY_CALL_EXCEPTION: {
                                consts.KEY_EXCEPTION: LaymanError,
                                consts.KEY_EXCEPTION_ASSERTS: [
                                    Action(processing.exception.response_exception, {'expected': exp_exception}, ),
                                ],
                            }, },
                        consts.KEY_FINAL_ASSERTS: [
                            *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                        ]
                    }
                    patch.append(action_def)
                else:
                    action_def = {
                        consts.KEY_ACTION: {
                            consts.KEY_CALL: Action(process_client.patch_workspace_publication,
                                                    {**tc_params[KEY_ACTION_PARAMS],
                                                     **patch_params.get(KEY_ACTION_PARAMS, {}),
                                                     **rest_param_dict}),
                            consts.KEY_RESPONSE_ASSERTS: [
                                Action(processing.response.valid_post, {}),
                            ],
                        },
                        consts.KEY_FINAL_ASSERTS: [
                            Action(publication.rest.async_error_in_info_key, {'info_key': failed_info_key,
                                                                              'expected': exp_exception, }, ),
                        ],
                    }
                    if assert_no_bbox_and_crs:
                        action_def[consts.KEY_FINAL_ASSERTS].append(Action(publication.internal.no_bbox_and_crs, {}))

                    patch.append(action_def)
                    patch.append(VALIDATION_PATCH_ACTION)
                publ_name = f"{testcase}_patch_{patch_key}{test_case_postfix}"
                result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], publ_name)] = patch

    return result
