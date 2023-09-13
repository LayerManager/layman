from copy import deepcopy
import os
import pytest

from layman.layer.filesystem import gdal
from test_tools import process_client
from tests import EnumTestTypes, Publication, EnumTestKeys
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
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        'expected_input': {
            'color_interpretations': ['Gray'],
            'nodata': None,
            'min': 178,
            'max': 205,
        },
    },
    'tif_byte_0_min_max_nd': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        'expected_input': {
            'color_interpretations': ['Gray'],
            'nodata': 255,
            'min': 228,
            'max': 254,
        },
    },
    'tif_byte_0_nd_min_max': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        'expected_input': {
            'color_interpretations': ['Gray'],
            'nodata': 200,
            'min': 228,
            'max': 254,
        },
    },
    'tif_byte_nd_min0_max': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        'expected_input': {
            'color_interpretations': ['Gray'],
            'nodata': -999,
            'min': 0,
            'max': 40,
        },
    },
    'tif_byte_nd0_min_max': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        'expected_input': {
            'color_interpretations': ['Gray'],
            'nodata': 0,
            'min': 2,
            'max': 20,
        },
    },
    'tif_byte_0_min_nd_max': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        'expected_input': {
            'color_interpretations': ['Gray'],
            'nodata': 10,
            'min': 1,
            'max': 27,
        },
    },
    'tif_float_min_0_max_nd': {
        'expected_input': {
            'color_interpretations': ['Gray'],
            'nodata': 3.4028234663852886e+38,
            'min': -0.2364,
            'max': 0.8629,
            'tolerance': 0.0001,
        },
    },
    'tif_float_alpha_min_0_max': {
        'expected_input': {
            'color_interpretations': ['Gray', 'Alpha'],
            'nodata': None,
            'min': -0.2364,
            'max': 0.8629,
            'tolerance': 0.0001,
        },
    },
    'timeseries': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        'rest_args': {
            'file_paths': [
                'timeseries/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                'timeseries/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.TIF',
            ],
            'time_regex': r'[0-9]{8}T[0-9]{6}',
        },
        'expected_input': {
            'timeseries/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif': {
                'color_interpretations': ['Gray'],
                'nodata': 255,
                'min': 82,
                'max': 186,
            },
            'timeseries/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.TIF': {
                'color_interpretations': ['Gray'],
                'nodata': 255,
                'min': 64,
                'max': 186,
            },
        },
    },
}


def prepare_test_case(key):
    all_params = deepcopy(TEST_CASES[key])

    base_file_name = key

    rest_args = all_params.pop('rest_args', {})
    rest_args.setdefault('file_paths', [f"{base_file_name}.{base_file_name.split('_')[0]}"])
    rest_args['file_paths'] = [os.path.join(DIRECTORY, fp) for fp in rest_args['file_paths']]
    test_type = all_params.pop(EnumTestKeys.TYPE, EnumTestTypes.MANDATORY)

    return base_test.TestCaseType(key=key, type=test_type, params=all_params, rest_args=rest_args,
                                  marks=[pytest.mark.xfail(reason="Not yet implemented.")]
                                  if all_params.get('xfail') else [],
                                  )


def assert_input_file(file_path, expected_values):
    assert gdal.get_color_interpretations(file_path) == expected_values['color_interpretations']

    assert gdal.get_nodata_value(file_path) == expected_values['nodata']

    min_value, max_value = gdal.get_statistics(file_path)[0]
    tolerance = expected_values.get('tolerance', 0)
    assert min_value == pytest.approx(expected_values['min'], tolerance)
    assert max_value == pytest.approx(expected_values['max'], tolerance)


class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_layer_raster_contrast'

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = [
        base_test.RestMethod,
    ]

    test_cases = [prepare_test_case(key) for key in TEST_CASES]

    @staticmethod
    def test_contrast(layer: Publication, params, rest_method, rest_args):
        """Parametrized using pytest_generate_tests"""

        expected_input = params['expected_input']
        for abs_file_path in rest_args['file_paths']:
            rel_file_path = os.path.relpath(abs_file_path, DIRECTORY)
            assert_input_file(abs_file_path, expected_input.get(rel_file_path, expected_input))

        rest_method.fn(layer, args=rest_args)

        assert_util.is_publication_valid_and_complete(layer)
        base_file_name = '_'.join(layer.name.split('_')[1:])
        exp_thumbnail = os.path.join(DIRECTORY, f"thumbnail_{base_file_name}.png")
        asserts_publ.internal.thumbnail_equals(layer.workspace, layer.type, layer.name, exp_thumbnail, max_diffs=1)
