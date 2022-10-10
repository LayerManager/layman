import os
import pytest

from layman.layer.filesystem import gdal
from test_tools import process_client
from tests import EnumTestTypes, Publication
from tests.asserts.final import publication as asserts_publ
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

TEST_CASES = {
    'tif_byte': {
        'expected_input': {
            'color_interpretations': ['Gray'],
            'nodata': None,
            'min': 228,
            'max': 255,
        }
    },
    'tif_float': {
        'expected_input': {
            'color_interpretations': ['Gray'],
            'nodata': None,
            'min': 178,
            'max': 205,
        }
    },
    'tif_byte_0_min_max_nd': {
        'expected_input': {
            'color_interpretations': ['Gray'],
            'nodata': 255,
            'min': 228,
            'max': 254,
        }
    },
    'tif_byte_0_nd_min_max': {
        'expected_input': {
            'color_interpretations': ['Gray'],
            'nodata': 200,
            'min': 228,
            'max': 254,
        }
    },
    'tif_byte_nd0_min_max': {
        'expected_input': {
            'color_interpretations': ['Gray'],
            'nodata': 0,
            'min': 2,
            'max': 20,
        }
    },
    'tif_byte_0_min_nd_max': {
        'expected_input': {
            'color_interpretations': ['Gray'],
            'nodata': 10,
            'min': 1,
            'max': 27,
        }
    },
}


def assert_input_file(file_path, expected_values):
    assert gdal.get_color_interpretations(file_path) == expected_values['color_interpretations']

    assert gdal.get_nodata_value(file_path) == expected_values['nodata']

    min_value, max_value, _, _ = gdal.get_statistics(file_path)[0]
    assert min_value == expected_values['min']
    assert max_value == expected_values['max']


class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_layer_raster_contrast'

    publication_type = process_client.LAYER_TYPE

    test_cases = [base_test.TestCaseType(key=key, type=EnumTestTypes.MANDATORY,
                                         marks=[pytest.mark.xfail(reason="Not yet implemented.")]
                                         if params.get('xfail') else []
                                         )
                  for key, params in TEST_CASES.items()]

    # pylint: disable=unused-argument
    @staticmethod
    def test_contrast(layer: Publication, key, params, rest_method):
        """Parametrized using pytest_generate_tests"""
        base_file_name = key
        file_name = f"{base_file_name}.{base_file_name.split('_')[0]}"
        file_path = os.path.join(DIRECTORY, file_name)
        assert_input_file(file_path, TEST_CASES[key]['expected_input'])
        layer_params = {
            'file_paths': [file_path],
        }
        rest_method(layer, params=layer_params)

        assert_util.is_publication_valid_and_complete(layer)
        base_file_name = '_'.join(layer.name.split('_')[1:])
        exp_thumbnail = os.path.join(DIRECTORY, f"thumbnail_{base_file_name}.png")
        asserts_publ.internal.thumbnail_equals(layer.workspace, layer.type, layer.name, exp_thumbnail, max_diffs=1)
