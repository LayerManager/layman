import os
import copy

import crs as crs_def
from tests.asserts import util as asserts_util
import tests.asserts.processing as processing
import tests.asserts.final.publication as publication
from test_tools import process_client, util
from ... import common_publications as publications
from ..... import Action, Publication, dynamic_data as consts

KEY_INFO_VALUES = 'info_values'
KEY_ONLY_FIRST_PARAMETRIZATION = 'only_first_parametrization'
KEY_ACTION_PARAMETRIZATION = 'action_parametrization'

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

REST_PARAMETRIZATION = {
    'with_chunks': {False: 'sync', True: 'chunks'},
    'compress': {False: '', True: 'zipped'},
    'style_file': {f'{DIRECTORY}/sample_point_cz.sld': 'sld', f'{DIRECTORY}/sample_point_cz.qml': 'qml'}
}

SOURCE_EPSG_CODES = {
    crs_def.EPSG_4326: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [16.6066275955110711, 49.1989353676069285, 16.6068125589999127, 49.1990477233154735],
            }
        },
        consts.KEY_ACTION: {
            'with_chunks': False,
            'compress': False,
        },
        KEY_ONLY_FIRST_PARAMETRIZATION: False,
        KEY_ACTION_PARAMETRIZATION: publications.DEFAULT_ACTIONS[:1],
    },
    crs_def.EPSG_3857: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [1848641.3277258177, 6308684.223766193, 1848661.9177672109, 6308703.364768417],
            }
        },
        consts.KEY_ACTION: {
            'with_chunks': False,
            'compress': False,
        },
        KEY_ONLY_FIRST_PARAMETRIZATION: False,
        KEY_ACTION_PARAMETRIZATION: publications.DEFAULT_ACTIONS[:1],
    },
    crs_def.EPSG_5514: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [-598214.7290553625207394, -1160319.8064114262815565, -598200.9321668159682304, -1160307.4425631782505661],
                'bounding_box': [1848640.4769060146, 6308683.577507495, 1848663.461145939, 6308704.681240051],
            }
        },
        KEY_ONLY_FIRST_PARAMETRIZATION: False,
    },
    crs_def.EPSG_32633: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [617041.7249990371, 5450813.311883376, 617055.1207238155, 5450825.813110342],
                'bounding_box': [1848641.1346210986, 6308683.9454576615, 1848662.0013466848, 6308703.5310932305]
            }
        },
    },
    crs_def.EPSG_32634: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [179985.4523066559922881, 5458866.6349301775917411, 179999.1353933966602199, 5458879.0886732628569007],
                'bounding_box': [1848640.784753341, 6308683.836580554, 1848662.7351645508, 6308704.081036061]
            }
        },
    },
    crs_def.EPSG_3034: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [4464506.1421598251909018, 2519866.8009202978573740, 4464518.7942008553072810, 2519878.8700591023080051],
                'bounding_box': [1848640.5623333207, 6308683.148403931, 1848662.1915096296, 6308704.001720284]
            }
        },
    },
    crs_def.EPSG_3035: {
        KEY_INFO_VALUES: {
            'exp_publication_detail': {
                'native_bounding_box': [4801864.984034311, 2920036.6864006906, 4801878.080408361,
                                        2920049.1861927817],
                'bounding_box': [1848640.5726391396, 6308683.141668934, 1848662.1874939075, 6308704.004922842]
            }
        },
    },
}

# expected coordinates manually copied from QGIS 3.16.2 in given EPSG
# point_id 1: northernmost vertex of fountain at Moravske namesti, Brno
EXP_POINT_COORDINATES = [
    (1, crs_def.EPSG_3857, (1848649.486, 6308703.297), 0.2),
    # ~5 meters! By default, GeoServer limits WFS output to 4 decimal places, about 10 m accuracy
    (1, crs_def.EPSG_4326, (16.60669976, 49.19904767), 0.00005),
    (1, crs_def.CRS_84, (16.60669976, 49.19904767), 0.00005),
    (1, crs_def.EPSG_32633, (617046.8503, 5450825.7990), 0.1),
    (1, crs_def.EPSG_32634, (179991.0748, 5458879.0878), 0.1),
    (1, crs_def.EPSG_5514, (-598208.8093, -1160307.4484), 0.1),
    (1, crs_def.EPSG_3034, (4464510.640810357, 2519878.8700591023), 0.1),
    (1, crs_def.EPSG_3035, (4801869.646727926, 2920049.1861927817), 0.1),
]

EXP_POINT_COORDINATES_GS_FIXES = {
    # Should be the same as for EPSG:4326, but for (so far) unknown reasons, wrong by about 300 m for data in EPSG:5514
    (crs_def.EPSG_5514, crs_def.CRS_84, 1): (16.6041, 49.1999)
}

EXP_POINT_COORDINATES_DB_FIXES = {
    (crs_def.EPSG_5514, crs_def.EPSG_3034, 1): (4464511.541476852, 2519881.9274773938),
    (crs_def.EPSG_5514, crs_def.EPSG_3035, 1): (4801870.58233825, 2920052.353109576),
    (crs_def.EPSG_3034, crs_def.EPSG_5514, 1): (-598210.3483076858, -1160310.3629643407),
    (crs_def.EPSG_3035, crs_def.EPSG_5514, 1): (-598210.3483076858, -1160310.3629643407),
}

EXP_WMS_PICTURES = [
    (crs_def.EPSG_3857, (1848629.922, 6308682.319, 1848674.659, 6308704.687), (601, 301), 'sld', '1.3.0', 2, ''),
    (crs_def.EPSG_3857, (1848629.922, 6308682.319, 1848674.659, 6308704.687), (601, 301), 'qml', '1.3.0', 2, ''),
    (crs_def.EPSG_3857, (1848621.712, 6308661.197, 1848698.933, 6308712.273), (381, 252), 'qml', '1.3.0', 4, '_low'),
    (crs_def.EPSG_4326, (49.198905759, 16.606580653, 49.199074214, 16.606874005), (560, 321), 'sld', '1.3.0', 2, ''),
    (crs_def.EPSG_4326, (49.198905759, 16.606580653, 49.199074214, 16.606874005), (560, 321), 'qml', '1.3.0', 2, ''),
    (crs_def.EPSG_4326, (49.198772323, 16.60647156231, 49.199170804, 16.607074027), (381, 252), 'qml', '1.3.0', 4.3, '_low'),
    (crs_def.EPSG_4326, (16.606580653, 49.198905759, 16.606874005, 49.199074214), (560, 321), 'sld', '1.1.1', 2, ''),
    (crs_def.EPSG_4326, (16.606580653, 49.198905759, 16.606874005, 49.199074214), (560, 321), 'qml', '1.1.1', 2, ''),
    (crs_def.EPSG_4326, (16.60647156231, 49.198772323, 16.607074027, 49.199170804), (381, 252), 'qml', '1.1.1', 4.3, '_low'),
    (crs_def.CRS_84, (16.606580653, 49.198905759, 16.606874005, 49.199074214), (560, 321), 'sld', '1.3.0', 2, ''),
    (crs_def.CRS_84, (16.606580653, 49.198905759, 16.606874005, 49.199074214), (560, 321), 'qml', '1.3.0', 2, ''),
    (crs_def.CRS_84, (16.60647156231, 49.198772323, 16.607074027, 49.199170804), (381, 252), 'qml', '1.3.0', 4.3, '_low'),
    (crs_def.CRS_84, (16.606580653, 49.198905759, 16.606874005, 49.199074214), (560, 321), 'sld', '1.1.1', 2, ''),
    (crs_def.CRS_84, (16.606580653, 49.198905759, 16.606874005, 49.199074214), (560, 321), 'qml', '1.1.1', 2, ''),
    (crs_def.CRS_84, (16.60647156231, 49.198772323, 16.607074027, 49.199170804), (381, 252), 'qml', '1.1.1', 4.3, '_low'),
    (crs_def.EPSG_5514, (-598222.071, -1160322.246, -598192.491, -1160305.260), (559, 321), 'sld', '1.3.0', 2, ''),
    (crs_def.EPSG_5514, (-598222.071, -1160322.246, -598192.491, -1160305.260), (559, 321), 'qml', '1.3.0', 2, ''),
    (crs_def.EPSG_5514, (-598236.981, -1160331.352, -598182.368, -1160295.230), (381, 252), 'sld', '1.3.0', 2, '_low'),
    (crs_def.EPSG_5514, (-598236.981, -1160331.352, -598182.368, -1160295.230), (381, 252), 'qml', '1.3.0', 4, '_low'),
    (crs_def.EPSG_32633, (617036.812, 5450809.904, 617060.659, 5450828.394), (414, 321), 'sld', '1.3.0', 2, ''),
    (crs_def.EPSG_32633, (617036.812, 5450809.904, 617060.659, 5450828.394), (414, 321), 'qml', '1.3.0', 2, ''),
    (crs_def.EPSG_32633, (617019.512, 5450805.336, 617071.525, 5450843.199), (397, 289), 'qml', '1.3.0', 4, '_low'),
    (crs_def.EPSG_32634, (179980.621, 5458862.472, 180005.430, 5458881.708), (415, 321), 'sld', '1.3.0', 2, ''),
    (crs_def.EPSG_32634, (179980.621, 5458862.472, 180005.430, 5458881.708), (415, 321), 'qml', '1.3.0', 2.6, ''),
    (crs_def.EPSG_32634, (179969.973, 5458859.204, 180018.657, 5458894.643), (397, 289), 'qml', '1.3.0', 4.2, '_low'),
]

EXP_BBOXES = {
    crs_def.EPSG_3857: {
        'bbox': [1848641.3277258177, 6308684.223766193, 1848661.9177672109, 6308703.364768417],
        'precision': 2,
    },
    crs_def.EPSG_4326: {
        'bbox': [16.6066275955110711, 49.1989353676069285, 16.6068125589999127, 49.1990477233154735],
        'precision': 0.00002,  # This is about 2 meters
    },
    crs_def.EPSG_5514: {
        'bbox': [-598214.7290553625207394, -1160319.8064114262815565, -598200.9321668159682304, -1160307.4425631782505661],
        'precision': 2,
    },
}


def use_low_resolution(wms_crs, crs, style_type):
    if style_type == 'sld':
        return False
    return (wms_crs == crs_def.EPSG_5514) != (crs == crs_def.EPSG_5514)


def generate(workspace=None):
    workspace = workspace or consts.COMMON_WORKSPACE

    result = dict()
    def_publ_info_values = {
        'exp_publication_detail': {
            'bounding_box': EXP_BBOXES[crs_def.EPSG_3857]['bbox'],
        },
        'file_extension': 'shp',
        'publ_type_detail': ('vector', 'sld'),
    }

    wms_picture_expected_number = len({(exp_wms_picture[0], exp_wms_picture[4], ) for exp_wms_picture in EXP_WMS_PICTURES})

    for crs, tc_params in SOURCE_EPSG_CODES.items():
        _, crs_code = crs.split(':')
        action_params = {
            'file_paths': [f'{DIRECTORY}/sample_point_cz_{crs_code}.{ext}' for ext in ['shp', 'dbf', 'prj', 'shx', 'cpg', ]
                           if os.path.exists(f'{DIRECTORY}/sample_point_cz_{crs_code}.{ext}')]
        }

        feature_spacial_precision_assert = [Action(publication.geoserver.feature_spatial_precision, {
            'feature_id': feature_id,
            'crs': wfs_crs,
            'exp_coordinates': EXP_POINT_COORDINATES_GS_FIXES.get((crs, wfs_crs, feature_id), exp_coordinates),
            'precision': precision,
        }) for feature_id, wfs_crs, exp_coordinates, precision in EXP_POINT_COORDINATES]

        db_spacial_precision_assert = [Action(
            publication.internal.point_coordinates,
            {
                'point_id': feature_id,
                'crs': to_crs,
                'exp_coordinates': EXP_POINT_COORDINATES_DB_FIXES.get((crs, to_crs, feature_id),
                                                                      exp_coordinates),
                'precision': precision,
            }
        ) for feature_id, to_crs, exp_coordinates, precision in EXP_POINT_COORDINATES
            if to_crs != crs_def.CRS_84]

        bboxes = copy.deepcopy(EXP_BBOXES)
        bboxes['CRS:84'] = copy.deepcopy(bboxes[crs_def.EPSG_4326])
        asserts_util.recursive_dict_update(bboxes, tc_params.get('bboxes', dict()))

        wms_bbox_actions = [
            Action(publication.geoserver.wms_bbox, {'exp_bbox': bbox['bbox'],
                                                    'crs': crs,
                                                    'precision': bbox['precision'],
                                                    })
            for crs, bbox in bboxes.items()
        ]

        action_parametrization = util.get_test_case_parametrization(param_parametrization=REST_PARAMETRIZATION,
                                                                    only_first_parametrization=tc_params.get(
                                                                        KEY_ONLY_FIRST_PARAMETRIZATION, True),
                                                                    default_params=tc_params.get(consts.KEY_ACTION),
                                                                    action_parametrization=tc_params.get(
                                                                        KEY_ACTION_PARAMETRIZATION, publications.DEFAULT_ACTIONS),
                                                                    )

        def_info_values = copy.deepcopy(def_publ_info_values)
        def_info_values['exp_publication_detail']['native_crs'] = crs
        asserts_util.recursive_dict_update(def_info_values, tc_params.get(KEY_INFO_VALUES, dict()))

        exp_thumbnail = f'{DIRECTORY}/sample_point_cz_{crs_code}_thumbnail.png'

        for test_case_postfix, action_method, action_predecessor, rest_param_dict in action_parametrization:
            wms_spacial_precision_assert = [Action(publication.geoserver.wms_spatial_precision, {
                'crs': wms_crs,
                'extent': extent,
                'img_size': img_size,
                'wms_version': wms_version,
                'diff_line_width': diff_line_width,
                'obtained_file_path': f'tmp/artifacts/test_spatial_precision_wms/sample_point_cz_{style_type}_{wms_crs.split(":")[1]}{suffix}.png',
                'expected_file_path': f'{DIRECTORY}/sample_point_cz_{wms_crs.split(":")[1]}{suffix}.png',
            })
                for wms_crs, extent, img_size, style_type, wms_version, diff_line_width, suffix in
                EXP_WMS_PICTURES
                if style_type == REST_PARAMETRIZATION['style_file'][rest_param_dict['style_file']]
                # If one and only one of the CRSs is 5514, use low resolution for QML style
                and (use_low_resolution(wms_crs, crs, style_type) == (suffix == '_low'))
            ]
            assert len(wms_spacial_precision_assert) == wms_picture_expected_number, \
                f'crs={crs}, \n' \
                f'wms_picture_expected_number={wms_picture_expected_number}, \n' \
                f'len(wms_spacial_precision_assert)={len(wms_spacial_precision_assert)}, \n' \
                f'wms_spacial_precision_assert={wms_spacial_precision_assert}'

            publ_name = "_".join([part for part in ['points', f'{crs_code}', test_case_postfix] if part])

            post_info_values = copy.deepcopy(def_info_values)
            post_info_values['exp_publication_detail']['native_crs'] = crs
            if rest_param_dict.get('compress'):
                post_info_values['gdal_prefix'] = '/vsizip/'
                post_info_values['file_extension'] = f'zip/sample_point_cz_{crs_code}.shp'
            if rest_param_dict.get('style_file'):
                post_info_values['publ_type_detail'] = ('vector', REST_PARAMETRIZATION['style_file'][rest_param_dict['style_file']])

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
                    *feature_spacial_precision_assert,
                    *wms_spacial_precision_assert,
                    Action(publication.internal.detail_3857bbox_value, {'exp_bbox': bboxes[crs_def.EPSG_3857]['bbox'],
                                                                        'precision': bboxes[crs_def.EPSG_3857]['precision'],
                                                                        }),
                    Action(publication.geoserver.wfs_bbox, {'exp_bbox': bboxes['CRS:84']['bbox'],
                                                            'precision': bboxes['CRS:84']['precision'],
                                                            }),
                    Action(publication.geoserver.wms_geographic_bbox, {'exp_bbox': bboxes['CRS:84']['bbox'],
                                                                       'precision': bboxes['CRS:84']['precision'],
                                                                       }),
                    *wms_bbox_actions,
                    *db_spacial_precision_assert,
                ]
            }
            actions_list = copy.deepcopy(action_predecessor)
            actions_list.append(action_def)
            result[Publication(workspace, process_client.LAYER_TYPE, publ_name)] = actions_list
    return result
