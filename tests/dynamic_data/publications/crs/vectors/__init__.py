import os
import copy

from tests.asserts import util as asserts_util
import tests.asserts.processing as processing
import tests.asserts.final.publication as publication
from test_tools import process_client
from ... import util, common_layers as layers
from ..... import Action, Publication, dynamic_data as consts

KEY_INFO_VALUES = 'info_values'

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

# expected coordinates manually copied from QGIS 3.16.2 in given EPSG
# point_id 1: northernmost vertex of fountain at Moravske namesti, Brno
EXP_POINT_COORDINATES = [
    (1, 3857, (1848649.486, 6308703.297), 0.2),
    # ~5 meters! By default, GeoServer limits WFS output to 4 decimal places, about 10 m accuracy
    (1, 4326, (16.60669976, 49.19904767), 0.00005),
    (1, 32633, (617046.8503, 5450825.7990), 0.1),
    (1, 32634, (179991.0748, 5458879.0878), 0.1),
    (1, 5514, (-598208.8093, -1160307.4484), 0.1),
]

EXP_WMS_PICTURES = [
    (3857, (1848629.922, 6308682.319, 1848674.659, 6308704.687), (601, 301), 'sld', '1.3.0', 2, ''),
    (3857, (1848629.922, 6308682.319, 1848674.659, 6308704.687), (601, 301), 'qml', '1.3.0', 2, ''),
    (4326, (49.198905759, 16.606580653, 49.199074214, 16.606874005), (560, 321), 'sld', '1.3.0', 2, ''),
    (4326, (49.198905759, 16.606580653, 49.199074214, 16.606874005), (560, 321), 'qml', '1.3.0', 2, ''),
    (4326, (16.606580653, 49.198905759, 16.606874005, 49.199074214), (560, 321), 'sld', '1.1.1', 2, ''),
    (4326, (16.606580653, 49.198905759, 16.606874005, 49.199074214), (560, 321), 'qml', '1.1.1', 2, ''),
    (5514, (-598222.071, -1160322.246, -598192.491, -1160305.260), (559, 321), 'sld', '1.3.0', 2, ''),
    # (5514, (-598222.071, -1160322.246, -598192.491, -1160305.260), (559, 321), 'qml', '1.3.0', 2, ''),
    (5514, (-598236.981, -1160331.352, -598182.368, -1160295.230), (381, 252), 'sld', '1.3.0', 2, '_low'),
    (5514, (-598236.981, -1160331.352, -598182.368, -1160295.230), (381, 252), 'qml', '1.3.0', 4, '_low'),
    (32633, (617036.812, 5450809.904, 617060.659, 5450828.394), (414, 321), 'sld', '1.3.0', 2, ''),
    (32633, (617036.812, 5450809.904, 617060.659, 5450828.394), (414, 321), 'qml', '1.3.0', 2, ''),
    (32634, (179980.621, 5458862.472, 180005.430, 5458881.708), (415, 321), 'sld', '1.3.0', 2, ''),
    (32634, (179980.621, 5458862.472, 180005.430, 5458881.708), (415, 321), 'qml', '1.3.0', 2, ''),
]


def generate(workspace=None):
    workspace = workspace or consts.COMMON_WORKSPACE

    result = dict()
    def_publ_info_values = {
        'exp_publication_detail': {
            'bounding_box': [1848641.3277258177, 6308684.223766193, 1848661.9177672109, 6308703.364768417],
        },
        'file_extension': 'shp',
        'publ_type_detail': ('vector', 'sld'),
    }

    feature_spacial_precision_assert = [Action(publication.geoserver.feature_spatial_precision, {
        'feature_id': feature_id,
        'epsg_code': epsg_code,
        'exp_coordinates': exp_coordinates,
        'precision': precision,
    }) for feature_id, epsg_code, exp_coordinates, precision in EXP_POINT_COORDINATES]

    for epsg_code, tc_params in SOURCE_EPSG_CODES.items():
        action_params = {
            'file_paths': [f'{DIRECTORY}/sample_point_cz_{epsg_code}.{ext}' for ext in ['shp', 'dbf', 'prj', 'shx', 'cpg', ]
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
            wms_spacial_precision_assert = [Action(publication.geoserver.wms_spatial_precision, {
                'epsg_code': epsg_code,
                'extent': extent,
                'img_size': img_size,
                'wms_version': wms_version,
                'diff_line_width': diff_line_width,
                'obtained_file_path': f'tmp/artifacts/test_spatial_precision_wms/sample_point_cz_{style_type}_{epsg_code}{suffix}.png',
                'expected_file_path': f'{DIRECTORY}/sample_point_cz_{epsg_code}{suffix}.png',
            })
                for epsg_code, extent, img_size, style_type, wms_version, diff_line_width, suffix in
                EXP_WMS_PICTURES
                if style_type == rest_param_dict.get('style_file')
            ]

            for action_code, action_method, action_predecessor in [
                ('post', process_client.publish_workspace_publication, []),
                ('patch', process_client.patch_workspace_publication, [layers.DEFAULT_POST])
            ]:
                test_case_postfix = '_'.join([REST_PARAMETRIZATION[key][value]
                                              for key, value in rest_param_dict.items()
                                              if REST_PARAMETRIZATION[key][value]])
                publ_name = "_".join([part for part in ['points', f'{epsg_code}', action_code, test_case_postfix] if part])
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
                    ]
                }
                actions_list = copy.deepcopy(action_predecessor)
                actions_list.append(action_def)
                result[Publication(workspace, process_client.LAYER_TYPE, publ_name)] = actions_list
    return result
