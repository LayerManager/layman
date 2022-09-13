import os
import pytest

from test_tools import process_client
from tests import TestTypes
from tests.asserts.final import publication as asserts_publ
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

RASTER_FILES = [
    'tif_byte',
    'tif_byte_nodata',
]


class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_layer_raster_contrast'

    publication_type = process_client.LAYER_TYPE

    test_cases = [base_test.TestCaseType(key=base_file_name, type=TestTypes.MANDATORY,
                                         marks=[pytest.mark.xfail(reason="Not yet implemented.")])
                  for base_file_name in RASTER_FILES]

    # pylint: disable=unused-argument
    @staticmethod
    def test_contrast(layer, key, params, rest_method):
        """Parametrized using pytest_generate_tests"""
        print(f"layer={layer}")
        base_file_name = key
        file_name = f"{base_file_name}.{base_file_name.split('_')[0]}"
        layer_params = {
            'file_paths': [os.path.join(DIRECTORY, file_name)],
        }
        rest_method(layer, params=layer_params)

        assert_util.is_publication_valid_and_complete(layer)
        base_file_name = os.path.splitext(file_name)[0]
        exp_thumbnail = os.path.join(DIRECTORY, f"thumbnail_{base_file_name}.png")
        asserts_publ.internal.thumbnail_equals(layer.workspace, layer.type, layer.name, exp_thumbnail, max_diffs=1)
