import os

import crs as crs_def
from test_tools import process_client
from tests.dynamic_data import base_test
from tests import EnumTestTypes, Publication4Test
from tests.asserts.final.publication import util as assert_util
from tests.asserts.final.publication.geoserver import feature_spatial_precision, wfs_bbox, wms_geographic_bbox
from tests.asserts.final.publication.internal import correct_values_in_detail, thumbnail_equals, \
    detail_3857bbox_value
from tests.asserts.processing.response import valid_post
from .. import common_publications as publications

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests


EXP_LATVIA_BBOXES = {
    'detail_3857': ([2683694.415110543, 7750959.738378579, 2683726.18235363, 7750991.711694677], 1),
    'wfs_bbox': ([24.1080371100000015, 56.9551622299999991, 24.1083224800000018, 56.9553188499999976], 0.000001),
    'wms_geographic_bbox': ([24.1080371100000015, 56.9551622299999991, 24.1083224800000018, 56.9553188499999976], 0.000001),
}


EXP_LATVIA_FEATURE_COORDINATES = [
    # feature_id, out_crs, exp_coordinates, precision
    (1, crs_def.EPSG_4326, (24.10803711, 56.95521220), 0.00004),
    (1, crs_def.EPSG_3059, (506570.91, 312405.56), 1),
]


TEST_CASES = {
    'epsg_4326_shp': {
        'filename': 'small_layer_4326',
        'rest_args': {},
        'correct_values_in_detail_params': {
            **publications.SMALL_LAYER.info_values,
            'file_extension': 'shp',
        },
        'exp_thumbnail': publications.SMALL_LAYER.thumbnail,
        'thumbnail_tolerance': 5,
        'exp_bboxes': {},
        'exp_feature_coordinates': {},
    },
    'epsg_4326_ne': {
        'filename': 'small_layer_4326_ne',
        'rest_args': {},
        'correct_values_in_detail_params': {
            **publications.SMALL_LAYER.info_values,
            'file_extension': 'shp',
        },
        'exp_thumbnail': publications.SMALL_LAYER.thumbnail,
        'thumbnail_tolerance': 5,
        'exp_bboxes': {},
        'exp_feature_coordinates': {},
    },
    'latvia_4326': {
        'filename': 'sample_point_la_4326',
        'rest_args': {
            'style_file': f'{DIRECTORY}/vectors/sample_point_cz.sld',
        },
        'correct_values_in_detail_params': {
            'exp_publication_detail': {
                'bounding_box': [2683694.415110543, 7750959.738378579, 2683726.18235363, 7750991.711694677],
                'native_crs': 'EPSG:4326',
                'native_bounding_box': [24.1080371100000015, 56.9551622299999991, 24.1083224800000018, 56.9553188499999976],
            },
            'file_extension': 'shp',
            'publ_type_detail': ('vector', 'sld'),
        },
        'exp_thumbnail': f'{DIRECTORY}/sample_point_la_4326_thumbnail.png',
        'thumbnail_tolerance': 279,
        'exp_bboxes': EXP_LATVIA_BBOXES,
        'exp_feature_coordinates': EXP_LATVIA_FEATURE_COORDINATES,
    },
    'latvia_4326_qml': {
        'filename': 'sample_point_la_4326',
        'rest_args': {
            'style_file': f'{DIRECTORY}/vectors/sample_point_cz.qml',
        },
        'correct_values_in_detail_params': {
            'exp_publication_detail': {
                'bounding_box': [2683694.415110543, 7750959.738378579, 2683726.18235363, 7750991.711694677],
                'native_crs': 'EPSG:4326',
                'native_bounding_box': [24.1080371100000015, 56.9551622299999991, 24.1083224800000018, 56.9553188499999976],
            },
            'file_extension': 'shp',
            'publ_type_detail': ('vector', 'qml'),
        },
        'exp_thumbnail': f'{DIRECTORY}/sample_point_la_4326_thumbnail.png',
        'thumbnail_tolerance': 5,
        'exp_bboxes': EXP_LATVIA_BBOXES,
        'exp_feature_coordinates': EXP_LATVIA_FEATURE_COORDINATES,
    },
    'latvia_3059': {
        'filename': 'sample_point_la_3059',
        'rest_args': {
            'style_file': f'{DIRECTORY}/vectors/sample_point_cz.sld',
        },
        'correct_values_in_detail_params': {
            'exp_publication_detail': {
                'bounding_box': [2683694.3990728464, 7750959.722238572, 2683726.1999545163, 7750991.729864702],
                'native_crs': 'EPSG:3059',
                'native_bounding_box': [506570.9055767511, 312400.0189709142, 506588.25283597945, 312417.4443366183],
            },
            'file_extension': 'shp',
            'publ_type_detail': ('vector', 'sld'),
        },
        'exp_thumbnail': f'{DIRECTORY}/sample_point_la_3059_thumbnail.png',
        'thumbnail_tolerance': 5,
        'exp_bboxes': EXP_LATVIA_BBOXES,
        'exp_feature_coordinates': EXP_LATVIA_FEATURE_COORDINATES,
    },
    'latvia_3059_qml': {
        'filename': 'sample_point_la_3059',
        'rest_args': {
            'style_file': f'{DIRECTORY}/vectors/sample_point_cz.qml',
        },
        'correct_values_in_detail_params': {
            'exp_publication_detail': {
                'bounding_box': [2683694.3990728464, 7750959.722238572, 2683726.1999545163, 7750991.729864702],
                'native_crs': 'EPSG:3059',
                'native_bounding_box': [506570.9055767511, 312400.0189709142, 506588.25283597945, 312417.4443366183],
            },
            'file_extension': 'shp',
            'publ_type_detail': ('vector', 'qml'),
        },
        'exp_thumbnail': f'{DIRECTORY}/sample_point_la_3059_qml_thumbnail.png',
        'thumbnail_tolerance': 5,
        'exp_bboxes': EXP_LATVIA_BBOXES,
        'exp_feature_coordinates': EXP_LATVIA_FEATURE_COORDINATES,
    },
}


class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_ws_crs'

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = []

    test_cases = [base_test.TestCaseType(
        key=key,
        type=EnumTestTypes.MANDATORY,
        rest_args={
            'file_paths': [file_path for file_path in [f"{DIRECTORY}/{value['filename']}.{ext}"
                                                       for ext in ['shp', 'dbf', 'prj', 'shx', 'cpg']]
                           if os.path.exists(file_path)],
            **value['rest_args'],
        },
        params=value,
    ) for key, value in TEST_CASES.items()]

    @staticmethod
    def test_precision(layer: Publication4Test, params, rest_method, rest_args):
        """Parametrized using pytest_generate_tests"""
        # publish layer
        response = rest_method.fn(layer, args=rest_args)

        # basic checks
        valid_post(*layer, response)
        assert_util.is_publication_valid_and_complete(layer)
        correct_values_in_detail(*layer, **params['correct_values_in_detail_params'])

        # thumbnail
        thumbnail_equals(*layer, exp_thumbnail=params['exp_thumbnail'], max_diffs=params['thumbnail_tolerance'])

        for key, (exp_bbox, precision) in params['exp_bboxes'].items():
            assert_method = {
                'detail_3857': detail_3857bbox_value,
                'wfs_bbox': wfs_bbox,
                'wms_geographic_bbox': wms_geographic_bbox,
            }[key]
            assert_method(*layer, exp_bbox=exp_bbox, precision=precision)

        for feature_id, out_crs, exp_coordinates, precision in params['exp_feature_coordinates']:
            feature_spatial_precision(*layer, feature_id=feature_id, crs=out_crs, exp_coordinates=exp_coordinates,
                                      precision=precision)
