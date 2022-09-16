import os

from layman import util as layman_util, app
from test_tools import process_client
from tests import TestTypes, Publication
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

DEFAULT_TIME_REGEXP = r'[0-9]{8}T[0-9]{9}Z(\?!.\*[0-9]{8}T[0-9]{9}Z.\*)'

LAYERS = {
    'default': {
        'params': {
            'time_regex': DEFAULT_TIME_REGEXP,
            'file_paths': ['sample/layman.layer/sample_tif_colortable_nodata.tif'],
        }
    },
}


class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_timeseries_layer'

    publication_type = process_client.LAYER_TYPE

    test_cases = [base_test.TestCaseType(key=name,
                                         type=TestTypes.MANDATORY,
                                         params=test_case_params.get('params', {}),
                                         ) for name, test_case_params in LAYERS.items()]

    # pylint: disable=unused-argument
    @staticmethod
    def test_timeseries_layer(layer: Publication, key, params, rest_method):
        """Parametrized using pytest_generate_tests"""
        layer_params = {
            **params,
        }
        rest_method(layer, params=layer_params)

        assert_util.is_publication_valid_and_complete(layer)

        with app.app_context():
            internal_info = layman_util.get_publication_info(layer.workspace, layer.type, layer.name, context={'keys': ['image_mosaic'], })
            rest_info = process_client.get_workspace_layer(layer.workspace, layer.name)
        assert internal_info['image_mosaic'] is True, f'internal_info={internal_info}'
        assert rest_info['image_mosaic'] is True, f'rest_info={rest_info}'
