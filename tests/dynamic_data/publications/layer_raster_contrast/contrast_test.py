import os
import pytest

from test_tools import process_client
from tests import TestTypes, Publication
from tests.asserts.final import publication as asserts_publ
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

TEST_CASES = {
    'tif_byte': {},
    'tif_float': {},
    'tif_byte_nodata_high': {},  # nodata > max value
    'tif_byte_nodata_low': {},  # nodata < min value
    'tif_byte_nodata_middle': {},  # min value < nodata < max value
    'tif_float_zero_nodata': {},  # min value < 0 < max value < nodata
}


class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_layer_raster_contrast'

    publication_type = process_client.LAYER_TYPE

    test_cases = [base_test.TestCaseType(key=key, type=TestTypes.MANDATORY,
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
        layer_params = {
            'file_paths': [os.path.join(DIRECTORY, file_name)],
        }
        rest_method(layer, params=layer_params)

        assert_util.is_publication_valid_and_complete(layer)
        base_file_name = '_'.join(layer.name.split('_')[1:])
        exp_thumbnail = os.path.join(DIRECTORY, f"thumbnail_{base_file_name}.png")
        asserts_publ.internal.thumbnail_equals(layer.workspace, layer.type, layer.name, exp_thumbnail, max_diffs=1)
