import os
import pytest

from test_tools import process_client
from tests import EnumTestTypes, Publication, EnumTestKeys
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

TEST_CASES = {
    'default_sld': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        'exp_version': '1.0.0',
    },
    'sld_1_1_0': {
        'style_file': 'sample/style/sld_1_1_0.xml',
        'exp_version': '1.0.0',
    },
    'sld_1_0_0': {
        'style_file': 'sample/style/basic.sld',
        'exp_version': '1.0.0',
    },
    'qml': {
        'style_file': 'sample/style/small_layer.qml',
        'exp_version': '3.16.3-Hannover',
    },
}


class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_layer_style'

    publication_type = process_client.LAYER_TYPE

    test_cases = [base_test.TestCaseType(key=key,
                                         type=value.get(EnumTestKeys.TYPE, EnumTestTypes.MANDATORY),
                                         params=value,
                                         marks=[pytest.mark.xfail(reason="Not yet implemented.")]
                                         if value.get('xfail') else []
                                         ) for key, value in TEST_CASES.items()]

    # pylint: disable=unused-argument
    @staticmethod
    def test_style_xml(layer: Publication, key, params, rest_method):
        """Parametrized using pytest_generate_tests"""
        rest_method(layer, params={
            'file_paths': ['sample/layman.layer/small_layer.geojson'],
            'style_file': params.get('style_file'),
        })

        assert_util.is_publication_valid_and_complete(layer)
        style = process_client.get_workspace_layer_style(layer.workspace, layer.name)
        root = style.getroot()
        assert root.attrib['version'] == params['exp_version']
