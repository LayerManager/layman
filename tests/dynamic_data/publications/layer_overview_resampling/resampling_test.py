import os
from layman import settings
from test_tools import process_client
from tests.asserts.final import publication as asserts_publ
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests


class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_overview_resampling_layer'

    publication_type = process_client.LAYER_TYPE

    test_cases = {resampling_method: {} for resampling_method in settings.OVERVIEW_RESAMPLING_METHOD_LIST}

    # pylint: disable=unused-argument
    @staticmethod
    def test_overview_resampling(layer, key, params, rest_method):
        """Parametrized using pytest_generate_tests"""
        overview_resampling_method = key
        layer_params = {
            'file_paths': [os.path.join(DIRECTORY, 'raster_for_resampling.tif')],
            'overview_resampling': overview_resampling_method,
            'style_file': os.path.join(DIRECTORY, 'style.sld'),
        }
        rest_method(layer, params=layer_params)

        assert_util.is_publication_valid_and_complete(layer)
        exp_thumbnail = os.path.join(DIRECTORY, f"thumbnail_{overview_resampling_method}.png")
        asserts_publ.internal.thumbnail_equals(layer.workspace, layer.type, layer.name, exp_thumbnail, max_diffs=1)
