import os
import pytest

from test_tools import process_client
from tests import EnumTestTypes, EnumTestKeys
from tests.asserts.final import publication as asserts_publ
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

LAYERS = {
    'vector_sld': dict(),
    'vector_qml': {
        'rest_params': {
            'style_file': 'sample/style/small_layer.qml'},
        'expected_data': {
            'legend': {
                base_test.TestSingleRestPublication.patch_publication.__name__: f'legend_vector_qml_patch.png'
            }
        }

    },
    'raster': {
        'rest_params': {
            'file_paths': [
                'sample/layman.layer/sample_tif_tfw_rgba_opaque.tfw',
                'sample/layman.layer/sample_tif_tfw_rgba_opaque.tif',
            ],
        }
    }
}


class TestLayer(base_test.TestSingleRestPublication):
    workspace = 'dynamic_test_workspace_standard_layer'

    publication_type = process_client.LAYER_TYPE

    test_cases = [base_test.TestCaseType(key=key,
                                         type=params.get(EnumTestKeys.TYPE, EnumTestTypes.MANDATORY),
                                         params=params,
                                         marks=[pytest.mark.xfail(reason="Not yet implemented.")]
                                         if params.get('xfail') else []
                                         )
                  for key, params in LAYERS.items()]

    @staticmethod
    def test_layer(layer, key, params, rest_method):
        """Parametrized using pytest_generate_tests"""
        rest_method(layer, params=params.get('rest_params', {}))

        assert_util.is_publication_valid_and_complete(layer)

        exp_legend_filepath = os.path.join(DIRECTORY,
                                           params.get('expected_data', dict()).get('legend', dict()).get(rest_method.__name__,
                                                                                                         f'legend_{key}.png'))
        asserts_publ.geoserver.wms_legend(layer.workspace, layer.type, layer.name,
                                          exp_legend=exp_legend_filepath,
                                          obtained_file_path=f'tmp/artifacts/test_wms_legend/{layer.name}/legend_{layer.name}.png',
                                          )
