import copy

from layman import LaymanError
from tests.asserts import util as asserts_util
import tests.asserts.processing as processing
import tests.asserts.final.publication as publication
from test_tools import process_client
from . import util
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
    'empty_zip': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [],
            'compress': True,
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'detail': {'parameter': 'file',
                                     'message': 'Zip file without data file inside.',
                                     'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg; or one of them in single .zip file.',
                                     'files': [
                                         'temporary_zip_file.zip',
                                     ],
                                     },
                          },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
                'detail': {'files': ['empty_zip_post_chunks_zipped.zip']}}
        },
    },
    'tif_with_qml': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': ['sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif'],
            'style_file': 'sample/style/ne_10m_admin_0_countries.qml',
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 48,
                          'message': 'Wrong combination of parameters',
                          'detail': 'Raster layers are not allowed to have QML style.',
                          },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
            }
        },
        KEY_PATCHES: {
            'data_and_style': {
                KEY_PATCH_POST: dict(),
                KEY_EXPECTED_EXCEPTION: {
                    frozenset([('compress', True), ('with_chunks', True)]): {
                        'sync': False,
                    },
                },
            },
            'data_without_style': {
                KEY_PATCH_POST: {
                    'file_paths': ['sample/layman.layer/sample_point_cz.geojson'],
                    'style_file': 'sample/layman.layer/sample_point_cz.qml',
                },
                KEY_ACTION_PARAMS: {
                    'style_file': None,
                },
                KEY_EXPECTED_EXCEPTION: {
                    frozenset([('compress', True), ('with_chunks', True)]): {
                        'sync': False,
                    },
                },
            },
        },
    },
    'non_readable_raster': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': ['test_tools/data/layers/non_readable_raster.tif'],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'message': 'Wrong parameter value',
                          'detail': {'parameter': 'file',
                                     'message': 'Unable to open raster file.',
                                     'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg; or one of them in single .zip file.',
                                     'file': '/layman_data_test/workspaces/dynamic_test_workspace_generated_wrong_input/layers/non_readable_raster_post_sync/input_file/non_readable_raster_post_sync.tif',
                                     },
                          },
            frozenset([('compress', True), ('with_chunks', False)]): {
                'detail': {'file': '/vsizip//layman_data_test/workspaces/dynamic_test_workspace_generated_wrong_input/layers/non_readable_raster_post_sync_zipped/input_file/non_readable_raster_post_sync_zipped.zip/non_readable_raster.tif',
                           }
            },
            frozenset([('compress', False), ('with_chunks', True)]): {
                'sync': False,
                'detail': {'file': '/layman_data_test/workspaces/dynamic_test_workspace_generated_wrong_input/layers/non_readable_raster_post_chunks/input_file/non_readable_raster_post_chunks.tif',
                           }
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
                'detail': {'file': '/vsizip//layman_data_test/workspaces/dynamic_test_workspace_generated_wrong_input/layers/non_readable_raster_post_chunks_zipped/input_file/non_readable_raster_post_chunks_zipped.zip/non_readable_raster.tif',
                           }
            },
        },
    },
}


def generate(workspace=None):
    workspace = workspace or consts.COMMON_WORKSPACE

    result = dict()
    for testcase, tc_params in TESTCASES.items():
        for rest_param_dict in util.dictionary_product(REST_PARAMETRIZATION):
            test_case_postfix = '_'.join([REST_PARAMETRIZATION[key][value]
                                          for key, value in rest_param_dict.items()
                                          if REST_PARAMETRIZATION[key][value]])
            if any(k in rest_param_dict and rest_param_dict[k] != v for k, v in tc_params[KEY_ACTION_PARAMS].items()):
                continue
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
            for rest_param_dict in util.dictionary_product(REST_PARAMETRIZATION):
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
                                                     **patch_params.get(KEY_ACTION_PARAMS, dict()),
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
                                                     **patch_params.get(KEY_ACTION_PARAMS, dict()),
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
