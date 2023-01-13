import os
import copy
import crs as crs_def
from test_tools import process_client, util
from tests.asserts import util as asserts_util
import tests.asserts.final.publication as publication
import tests.asserts.processing as processing
from ... import common_publications as publications
from ..... import Action, Publication, dynamic_data as consts


KEY_INFO_VALUES = 'info_values'
KEY_ONLY_FIRST_PARAMETRIZATION = 'only_first_parametrization'

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

REST_PARAMETRIZATION = {
    'with_chunks': {False: '', True: 'chunks'},
    'compress': {False: '', True: 'zipped'},
}

SOURCE_CRS = {
    crs_def.EPSG_4326: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [16.606587576736, 49.198911725592005, 16.606851456552, 49.199072702792],
                'bounding_box': [1848636.8728561546, 6308680.196100452, 1848666.2478229022, 6308707.6202965565],
            }
        },
    },
    crs_def.EPSG_3857: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [1848636.3811272, 6308680.1143396, 1848666.8389494002, 6308707.5628834],
                'bounding_box': [1848636.3811272, 6308680.1143396, 1848666.8389494002, 6308707.5628834],
            }
        },
    },
    crs_def.EPSG_5514: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [-598217.8828349999, -1160322.4535628, -598198.2786699999, -1160305.0114542001],
                'bounding_box': [1848635.2878977319, 6308679.0262031425, 1848667.9258161425, 6308708.821095935],
            }
        },
        KEY_ONLY_FIRST_PARAMETRIZATION: False,
    },
    crs_def.EPSG_32633: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [617038.822659, 5450810.940462001, 617058.1279862, 5450828.1348948],
                'bounding_box': [1848636.6245464054, 6308680.214995095, 1848666.6700974994, 6308707.182104623],
            }
        },
    },
    crs_def.EPSG_32634: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [179982.9579464, 5458864.3851908, 180001.7869064, 5458881.6025756],
                'bounding_box': [1848636.761700774, 6308680.177464705, 1848666.9742205392, 6308708.157743086],
            }
        },
    },
    crs_def.EPSG_3034: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [4464503.1786742, 2519864.4423224, 4464521.7093864, 2519881.639366],
                'bounding_box': [1848635.5622696981, 6308679.010490673, 1848667.1735165308, 6308708.795145725],
            }
        },
    },
    crs_def.EPSG_3035: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [4801862.1376458, 2920034.1033083997, 4801881.1769774, 2920052.2550572],
                'bounding_box': [1848635.8928185008, 6308678.776642735, 1848667.3134760845, 6308709.076431936],
            }
        },
    },
}


EXP_WMS_PICTURES = [
    (crs_def.EPSG_3857, (1848636.381, 6308680.114, 1848666.839, 6308707.563), (169, 171), '1.3.0'),
    (crs_def.EPSG_4326, (49.1989117, 16.6065876, 49.1990727, 16.6068515), (146, 100), '1.3.0'),
    (crs_def.EPSG_4326, (16.6065876, 49.1989117, 16.6068515, 49.1990727), (146, 100), '1.1.1'),
    (crs_def.CRS_84, (16.6065876, 49.1989117, 16.6068515, 49.1990727), (146, 100), '1.3.0'),
    (crs_def.CRS_84, (16.6065876, 49.1989117, 16.6068515, 49.1990727), (146, 100), '1.1.1'),
    (crs_def.EPSG_5514, (-598217.883, -1160322.454, -598198.279, -1160305.011), (161, 147), '1.3.0'),
    (crs_def.EPSG_32633, (617038.823, 5450810.940, 617058.128, 5450828.135), (148, 148), '1.3.0'),
    (crs_def.EPSG_32634, (179980.621, 5458862.472, 180005.430, 5458881.708), (150, 154), '1.3.0'),
]


EXP_BBOXES = {
    crs_def.EPSG_3857: {
        'bbox': [1848636.381, 6308680.114, 1848666.839, 6308707.563],
        'precision': 2,
    },
    crs_def.EPSG_4326: {
        'bbox': [16.6065876, 49.1989117, 16.6068515, 49.1990727],
        'precision': 0.00002,  # This is about 2 meters
    },
    crs_def.EPSG_5514: {
        'bbox': [-598217.883, -1160322.454, -598198.279, -1160305.011],
        'precision': 2.05,
    },
}


def generate(workspace=None):
    workspace = workspace or consts.COMMON_WORKSPACE

    result = dict()
    def_publ_info_values = {
        'exp_publication_detail': {
            'bounding_box': EXP_BBOXES[crs_def.EPSG_3857]['bbox'],
        },
        'file_extension': 'tif',
        'publ_type_detail': ('raster', 'sld'),
    }

    wms_picture_expected_number = len({(exp_wms_picture[0], exp_wms_picture[3],) for exp_wms_picture in EXP_WMS_PICTURES})

    for crs, tc_params in SOURCE_CRS.items():
        _, crs_code = crs.split(':')
        action_params = {
            'file_paths': [f'{DIRECTORY}/cz_{crs_code}.tif']
        }

        bboxes = copy.deepcopy(EXP_BBOXES)
        bboxes['CRS:84'] = copy.deepcopy(bboxes[crs_def.EPSG_4326])

        wms_bbox_actions = [
            Action(publication.geoserver.wms_bbox, {
                'exp_bbox': bbox['bbox'],
                'crs': crs,
                'precision': bbox['precision'],
                'contains': False,  # because bbox of each input raster is slightly different
            })
            for crs, bbox in bboxes.items()
        ]

        action_parametrization = util.get_test_case_parametrization(param_parametrization=REST_PARAMETRIZATION,
                                                                    only_first_parametrization=tc_params.get(
                                                                        KEY_ONLY_FIRST_PARAMETRIZATION, True),
                                                                    default_params=tc_params.get(consts.KEY_ACTION),
                                                                    action_parametrization=publications.DEFAULT_ACTIONS,
                                                                    )

        def_info_values = copy.deepcopy(def_publ_info_values)
        def_info_values['exp_publication_detail']['native_crs'] = crs
        asserts_util.recursive_dict_update(def_info_values, tc_params.get(KEY_INFO_VALUES, dict()))

        exp_thumbnail = f'{DIRECTORY}/cz_{crs_code}/thumbnail.png'

        for test_case_postfix, action_method, action_predecessor, rest_param_dict in action_parametrization:
            wms_spacial_precision_assert = [
                Action(publication.geoserver.wms_spatial_precision, {
                    'crs': wms_crs,
                    'extent': extent,
                    'img_size': img_size,
                    'wms_version': wms_version,
                    'diff_line_width': 0,
                    'obtained_file_path': f'tmp/artifacts/test_spatial_precision_wms/cz_raster_{crs_code}/{wms_crs.split(":")[1]}.png',
                    'expected_file_path': f'{DIRECTORY}/cz_{crs_code}/{wms_crs.split(":")[1]}.png',
                })
                for wms_crs, extent, img_size, wms_version in
                EXP_WMS_PICTURES
            ]
            assert len(wms_spacial_precision_assert) == wms_picture_expected_number, \
                f'crs={crs}, \n' \
                f'wms_picture_expected_number={wms_picture_expected_number}, \n' \
                f'len(wms_spacial_precision_assert)={len(wms_spacial_precision_assert)}, \n' \
                f'wms_spacial_precision_assert={wms_spacial_precision_assert}'

            publ_name = "_".join([part for part in ['raster', f'{crs_code}', test_case_postfix] if part])

            post_info_values = copy.deepcopy(def_info_values)
            post_info_values['exp_publication_detail']['native_crs'] = crs
            if rest_param_dict.get('compress'):
                post_info_values['gdal_prefix'] = '/vsizip/'
                post_info_values['file_extension'] = f'zip/cz_{crs_code}.tif'

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
                    *wms_spacial_precision_assert,
                    Action(publication.internal.detail_3857bbox_value, {
                        'exp_bbox': bboxes[crs_def.EPSG_3857]['bbox'],
                        'precision': bboxes[crs_def.EPSG_3857]['precision'],
                        'contains': False,  # because bbox of each input raster is slightly different
                    }),
                    Action(publication.geoserver.wms_geographic_bbox, {
                        'exp_bbox': bboxes['CRS:84']['bbox'],
                        'precision': bboxes['CRS:84']['precision'],
                        'contains': False,  # because bbox of each input raster is slightly different
                    }),
                    *wms_bbox_actions,
                ]
            }
            actions_list = copy.deepcopy(action_predecessor)
            actions_list.append(action_def)
            result[Publication(workspace, process_client.LAYER_TYPE, publ_name)] = actions_list
    return result
