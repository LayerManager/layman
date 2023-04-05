import os
import copy

import crs as crs_def
import tests.asserts.processing as processing
import tests.asserts.final.publication as publication
from test_tools import process_client, util
from . import vectors, rasters
from .. import common_publications as publications
from .... import Action, Publication, dynamic_data as consts

KEY_ACTION_PARAMS = 'action_params'
KEY_FILE_NAME = 'file_suffix'
KEY_INFO_VALUES = 'info_values'
KEY_THUMBNAIL = 'thumbnail'
KEY_ONLY_FIRST_PARAMETRIZATION = 'only_first_parametrization'

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

LA_FINAL_ASSERTS = [
    Action(publication.internal.detail_3857bbox_value,
           {'exp_bbox': [2683694.415110543, 7750959.738378579, 2683726.18235363, 7750991.711694677],
            'precision': 1,
            }),
    Action(publication.geoserver.wfs_bbox,
           {'exp_bbox': [24.1080371100000015, 56.9551622299999991, 24.1083224800000018, 56.9553188499999976],
            'precision': 0.000001,
            }),
    Action(publication.geoserver.wms_geographic_bbox,
           {'exp_bbox': [24.1080371100000015, 56.9551622299999991, 24.1083224800000018, 56.9553188499999976],
            'precision': 0.000001,
            }),
    Action(publication.geoserver.feature_spatial_precision, {
        'feature_id': 1,
        'crs': crs_def.EPSG_4326,
        'exp_coordinates': (24.10803711, 56.95521220),
        'precision': 0.00004,
    }),
    Action(publication.geoserver.feature_spatial_precision, {
        'feature_id': 1,
        'crs': crs_def.EPSG_3059,
        'exp_coordinates': (506570.91, 312405.56),
        'precision': 1,
    }),
]

REST_PARAMETRIZATION = {
    'with_chunks': {False: '', True: 'chunks'},
    'compress': {False: '', True: 'zipped'},
}

TESTCASES = {
    'epsg_4326_shp': {
        KEY_FILE_NAME: 'small_layer_4326',
        KEY_INFO_VALUES: {**publications.SMALL_LAYER.info_values,
                          'file_extension': 'shp', },
        KEY_THUMBNAIL: publications.SMALL_LAYER.thumbnail,
    },
    'epsg_4326_ne': {
        KEY_FILE_NAME: 'small_layer_4326_ne',
        KEY_INFO_VALUES: {**publications.SMALL_LAYER.info_values,
                          'file_extension': 'shp', },
        KEY_THUMBNAIL: publications.SMALL_LAYER.thumbnail,
    },
    'la_4326': {
        KEY_FILE_NAME: 'sample_point_la_4326',
        KEY_ACTION_PARAMS: {
            'style_file': f'{DIRECTORY}/vectors/sample_point_cz.sld',
        },
        KEY_INFO_VALUES: {'exp_publication_detail': {
            'bounding_box': [2683694.415110543, 7750959.738378579, 2683726.18235363, 7750991.711694677],
            'native_crs': 'EPSG:4326',
            'native_bounding_box': [24.1080371100000015, 56.9551622299999991, 24.1083224800000018, 56.9553188499999976],
        },
            'file_extension': 'shp',
            'publ_type_detail': ('vector', 'sld'), },
        KEY_THUMBNAIL: f'{DIRECTORY}/sample_point_la_4326_thumbnail.png',
        consts.KEY_FINAL_ASSERTS: LA_FINAL_ASSERTS,
    },
    'la_4326_qml': {
        KEY_FILE_NAME: 'sample_point_la_4326',
        KEY_ACTION_PARAMS: {
            'style_file': f'{DIRECTORY}/vectors/sample_point_cz.qml',
        },
        KEY_INFO_VALUES: {'exp_publication_detail': {
            'bounding_box': [2683694.415110543, 7750959.738378579, 2683726.18235363, 7750991.711694677],
            'native_crs': 'EPSG:4326',
            'native_bounding_box': [24.1080371100000015, 56.9551622299999991, 24.1083224800000018, 56.9553188499999976],
        },
            'file_extension': 'shp',
            'publ_type_detail': ('vector', 'qml'), },
        KEY_THUMBNAIL: f'{DIRECTORY}/sample_point_la_4326_thumbnail.png',
        consts.KEY_FINAL_ASSERTS: LA_FINAL_ASSERTS,
    },
    'la_3059': {
        KEY_FILE_NAME: 'sample_point_la_3059',
        KEY_ACTION_PARAMS: {
            'style_file': f'{DIRECTORY}/vectors/sample_point_cz.sld',
        },
        KEY_INFO_VALUES: {'exp_publication_detail': {
            'bounding_box': [2683694.3990728464, 7750959.722238572, 2683726.1999545163, 7750991.729864702],
            'native_crs': 'EPSG:3059',
            'native_bounding_box': [506570.9055767511, 312400.0189709142, 506588.25283597945, 312417.4443366183],
        },
            'file_extension': 'shp',
            'publ_type_detail': ('vector', 'sld'), },
        KEY_THUMBNAIL: f'{DIRECTORY}/sample_point_la_3059_thumbnail.png',
        consts.KEY_FINAL_ASSERTS: LA_FINAL_ASSERTS,
    },
    'la_3059_qml': {
        KEY_FILE_NAME: 'sample_point_la_3059',
        KEY_ACTION_PARAMS: {
            'style_file': f'{DIRECTORY}/vectors/sample_point_cz.qml',
        },
        KEY_INFO_VALUES: {'exp_publication_detail': {
            'bounding_box': [2683694.3990728464, 7750959.722238572, 2683726.1999545163, 7750991.729864702],
            'native_crs': 'EPSG:3059',
            'native_bounding_box': [506570.9055767511, 312400.0189709142, 506588.25283597945, 312417.4443366183],
        },
            'file_extension': 'shp',
            'publ_type_detail': ('vector', 'qml'), },
        KEY_THUMBNAIL: f'{DIRECTORY}/sample_point_la_3059_qml_thumbnail.png',
        consts.KEY_FINAL_ASSERTS: LA_FINAL_ASSERTS,
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

        action_parametrization = util.get_test_case_parametrization(param_parametrization=REST_PARAMETRIZATION,
                                                                    only_first_parametrization=tc_params.get(
                                                                        KEY_ONLY_FIRST_PARAMETRIZATION,
                                                                        True),
                                                                    default_params=action_params,
                                                                    action_parametrization=publications.DEFAULT_ACTIONS,
                                                                    )

        info_values = tc_params[KEY_INFO_VALUES]
        exp_thumbnail = tc_params[KEY_THUMBNAIL]

        for test_case_postfix, action_method, action_predecessor, rest_param_dict in action_parametrization:
            publ_name = "_".join([part for part in [testcase, test_case_postfix] if part])

            post_info_values = copy.deepcopy(info_values)
            if rest_param_dict.get('compress', False):
                post_info_values['gdal_prefix'] = '/vsizip/'
                post_info_values['file_extension'] = f'zip/{file_name}.shp'

            action_def = {
                consts.KEY_ACTION: {
                    consts.KEY_CALL: Action(action_method,
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
                    *tc_params.get(consts.KEY_FINAL_ASSERTS, []),
                ]
            }
            actions_list = copy.deepcopy(action_predecessor)
            actions_list.append(action_def)
            result[Publication(workspace, process_client.LAYER_TYPE, publ_name)] = actions_list

    return result


def generate(workspace=None):
    return {
        **generate_local(workspace),
        **vectors.generate(workspace + '_vectors'),
        **rasters.generate(workspace + '_rasters'),
    }
