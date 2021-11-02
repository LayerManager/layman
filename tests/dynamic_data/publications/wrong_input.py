import copy
import itertools

from layman import LaymanError
from tests.asserts import util as asserts_util
import tests.asserts.processing as processing
import tests.asserts.final.publication as publication
from test_tools import process_client
from ... import Action, Publication, dynamic_data as consts

KEY_PUBLICATION_TYPE = 'publ_type'
KEY_ACTION_PARAMS = 'action_params'
KEY_EXPECTED_EXCEPTION = 'expected_exception'
KEY_DEFAULT = 'default'
KEY_PATCHES = 'patches'
KEY_PATCH_POST = 'post_params'

REST_PARAMETRIZATION = {
    'with_chunks': {False: 'sync', True: 'chunks'},
    'compress': {False: '', True: 'zipped'},
}

TESTCASES = {
    'shp_without_dbf': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.cpg',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.README.html',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shx',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.VERSION.txt',
            ],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 18,
                          'message': 'Missing one or more ShapeFile files.',
                          'detail': {'missing_extensions': ['.dbf', '.prj'],
                                     'suggestion': 'Missing .prj file can be fixed also by setting "crs" parameter.',
                                     'path': 'ne_110m_admin_0_boundary_lines_land.shp',
                                     },
                          },
            frozenset([('compress', True), ('with_chunks', False)]): {
                'detail': {'path': 'temporary_zip_file.zip/ne_110m_admin_0_boundary_lines_land.shp'}},
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
                'detail': {'path': 'shp_without_dbf_post_chunks_zipped.zip/ne_110m_admin_0_boundary_lines_land.shp'}},
        },
        KEY_PATCHES: {
            'all_files': {
                KEY_PATCH_POST: dict(),
                KEY_EXPECTED_EXCEPTION: {
                    frozenset([('compress', True), ('with_chunks', False)]): {
                        'detail': {'path': 'temporary_zip_file.zip/ne_110m_admin_0_boundary_lines_land.shp'}},
                    frozenset([('compress', True), ('with_chunks', True)]): {
                        'sync': False,
                        'detail': {'path': 'shp_without_dbf_patch_all_files.zip/ne_110m_admin_0_boundary_lines_land.shp'}}
                },
            },
        },
    },
}


def generate(workspace=None):
    workspace = workspace or consts.COMMON_WORKSPACE

    rest_param_names = list(REST_PARAMETRIZATION.keys())
    rest_param_all_values = [list(REST_PARAMETRIZATION[p_name].keys()) for p_name in rest_param_names]

    result = dict()
    for testcase, tc_params in TESTCASES.items():
        for rest_param_values in itertools.product(*rest_param_all_values):
            test_case_postfix = '_'.join([REST_PARAMETRIZATION[rest_param_names[idx]][value]
                                          for idx, value in enumerate(rest_param_values)
                                          if REST_PARAMETRIZATION[rest_param_names[idx]][value]])
            rest_param_dict = {rest_param_names[idx]: value for idx, value in enumerate(rest_param_values)}
            rest_param_frozen_set = frozenset(rest_param_dict.items())
            default_exp_exception = copy.deepcopy(tc_params[KEY_EXPECTED_EXCEPTION][KEY_DEFAULT])
            exception_diff = tc_params[KEY_EXPECTED_EXCEPTION].get(rest_param_frozen_set, dict())
            exp_exception = asserts_util.recursive_dict_update(default_exp_exception, exception_diff)
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
                        Action(publication.internal.does_not_exist, dict())
                    ],
                }
            else:
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
                        Action(publication.rest.async_error_in_info_key, {'info_key': 'file',
                                                                          'expected': exp_exception, }, ),
                    ],
                }
            publ_name = f"{testcase}_post_{test_case_postfix}"
            result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], publ_name)] = [action_def]

        for patch_key, patch_params in tc_params.get(KEY_PATCHES, dict()).items():
            patch = [
                {
                    consts.KEY_ACTION: {
                        consts.KEY_CALL: Action(process_client.publish_workspace_publication,
                                                patch_params[KEY_PATCH_POST]),
                        consts.KEY_RESPONSE_ASSERTS: [
                            Action(processing.response.valid_post, dict()),
                        ],
                    },
                    consts.KEY_FINAL_ASSERTS: [
                        *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                    ]
                },
            ]
            for rest_param_values in itertools.product(*rest_param_all_values):
                rest_param_dict = {rest_param_names[idx]: value for idx, value in enumerate(rest_param_values)}
                rest_param_frozen_set = frozenset(rest_param_dict.items())
                default_exp_exception = copy.deepcopy(tc_params[KEY_EXPECTED_EXCEPTION][KEY_DEFAULT])
                exception_diff = patch_params[KEY_EXPECTED_EXCEPTION].get(rest_param_frozen_set, dict())
                exp_exception = asserts_util.recursive_dict_update(default_exp_exception, exception_diff)
                is_sync = exp_exception.pop('sync')
                if is_sync:
                    action_def = {
                        consts.KEY_ACTION: {
                            consts.KEY_CALL: Action(process_client.patch_workspace_publication,
                                                    {**tc_params[KEY_ACTION_PARAMS],
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
                else:
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
                            Action(publication.rest.async_error_in_info_key, {'info_key': 'file',
                                                                              'expected': exp_exception, }, ),
                        ],
                    }
                patch.append(action_def)
            result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], testcase + '_patch_' + patch_key)] = patch

    return result
