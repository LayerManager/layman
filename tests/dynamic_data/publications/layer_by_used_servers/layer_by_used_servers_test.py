from copy import deepcopy
import os
import pytest

from test_tools import process_client
from tests import EnumTestTypes
from tests.asserts.final import publication as asserts_publ
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

LAYERS = {
    'main': {
        'specific_params': {
            frozenset([base_test.LayerByUsedServers.LAYER_VECTOR_QML, base_test.RestMethod.POST]): {
                'expected_data': {
                    'legend': f'legend_vector_qml_post.png',
                },
            },
            frozenset([base_test.LayerByUsedServers.LAYER_VECTOR_QML, base_test.RestMethod.PATCH]): {
                'expected_data': {
                    'legend': f'legend_vector_qml_patch.png',
                },
            },
        },
    },
}


def generate_test_cases():
    tc_list = []
    for name, test_case_params in LAYERS.items():
        all_params = deepcopy(test_case_params)
        specific_params = all_params.pop('specific_params')
        test_case = base_test.TestCaseType(key=name,
                                           type=EnumTestTypes.MANDATORY,
                                           params=all_params,
                                           specific_params=specific_params,
                                           marks=[pytest.mark.xfail(reason="Not yet implemented.")]
                                           if test_case_params.get('xfail') else []
                                           )
        tc_list.append(test_case)
    return tc_list


class TestLayer(base_test.TestSingleRestPublication):
    workspace = 'dynamic_test_workspace_standard_layer'

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = [
        base_test.RestMethod,
        base_test.LayerByUsedServers,
    ]

    test_cases = generate_test_cases()

    @staticmethod
    def test_layer(layer, params, rest_args, rest_method, parametrization):
        """Parametrized using pytest_generate_tests"""
        publ_def = parametrization.publication_definition
        rest_method(layer, args=rest_args)

        assert_util.is_publication_valid_and_complete(layer)

        exp_legend_filename = params.get('expected_data', {}).get('legend')
        exp_legend_filepath = os.path.join(DIRECTORY, exp_legend_filename) if exp_legend_filename else publ_def.legend_image

        asserts_publ.geoserver.wms_legend(layer.workspace, layer.type, layer.name,
                                          exp_legend=exp_legend_filepath,
                                          obtained_file_path=f'tmp/artifacts/test_wms_legend/{layer.name}/legend_{layer.name}.png',
                                          )
        asserts_publ.geoserver_proxy.is_complete_in_workspace_wms(layer.workspace, layer.type, layer.name,
                                                                  version='1.1.1')
