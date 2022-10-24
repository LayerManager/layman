import os
import pytest

from test_tools import process_client
from tests import EnumTestTypes, Publication
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

TEST_CASES = {
    'issue_682': {
        'rest_params': {
            'file_paths': ['/code/sample/layman.layer/sample_tif_grayscale_alpha_nodata.tif'],
            'style_file': os.path.join(DIRECTORY, 'raster_float_grayscale_alpha_contrast_enhancement.sld'),
        }
    },
}


class TestFailingWms(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_geoserver_issues'

    publication_type = process_client.LAYER_TYPE

    test_cases = [base_test.TestCaseType(pytest_id=key, key=key, type=EnumTestTypes.OPTIONAL,
                                         params=params['rest_params'],
                                         marks=[pytest.mark.xfail(reason="Unknown GeoServer rendering issue.")]
                                         )
                  for key, params in TEST_CASES.items()]

    rest_parametrization = {
        'method': [
            base_test.RestMethodType('post_publication', 'post'),
        ],
    }

    # pylint: disable=unused-argument
    @staticmethod
    def test(layer: Publication, key, params, rest_method):
        """Parametrized using pytest_generate_tests"""

        rest_method(layer, params=params)
        assert_util.is_publication_valid_and_complete(layer)
