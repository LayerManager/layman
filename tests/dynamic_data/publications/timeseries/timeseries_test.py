import os

from test_tools import process_client
from tests import TestTypes, Publication
from tests.asserts.final.publication import util as assert_util, internal as assert_internal
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

DEFAULT_TIME_REGEXP = r'[0-9]{8}T[0-9]{9}Z(\?!.\*[0-9]{8}T[0-9]{9}Z.\*)'

LAYERS = {
    'default': {
        'params': {
            'time_regex': DEFAULT_TIME_REGEXP,
            'file_paths': ['sample/layman.layer/sample_tif_colortable_nodata.tif'],
        },
        'detail_values': {
            'exp_publication_detail': {
                'bounding_box': [868376.0, 522128.0, 940583.0, 593255.0],
                'native_crs': 'EPSG:3857',
                'native_bounding_box': [868376.0, 522128.0, 940583.0, 593255.0],
                'image_mosaic': True,
            },
            'file_extension': 'tif',
            'publ_type_detail': ('raster', 'sld'),
        },
    },
}


class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_timeseries_layer'

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = {
        'method': [
            base_test.RestMethodType('post_publication', 'post'),
        ],
    }

    test_cases = [base_test.TestCaseType(key=name,
                                         type=TestTypes.MANDATORY,
                                         params=test_case_params,
                                         ) for name, test_case_params in LAYERS.items()]

    # pylint: disable=unused-argument
    @staticmethod
    def test_timeseries_layer(layer: Publication, key, params, rest_method):
        """Parametrized using pytest_generate_tests"""
        rest_method(layer, params=params.get('params', {}))

        assert_util.is_publication_valid_and_complete(layer)

        assert_internal.correct_values_in_detail(layer.workspace, layer.type, layer.name,
                                                 **params.get('detail_values', {}),
                                                 )
