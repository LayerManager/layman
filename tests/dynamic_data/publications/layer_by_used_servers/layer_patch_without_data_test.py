from copy import deepcopy
from enum import Enum, unique
import os
import pytest

from layman import app, util as layman_util
from test_tools import process_client
from tests import EnumTestTypes
from tests.asserts.final.publication import util as assert_util
from tests.dynamic_data import base_test
from .. import Publication


@unique
class Key(Enum):
    PATCH_REST_ARGS = 'patch_rest_args'


DIRECTORY = os.path.dirname(os.path.abspath(__file__))
pytest_generate_tests = base_test.pytest_generate_tests
WORKSPACE = 'dynamic_test_workspace_standard_layer'

LAYERS = {
    'title': {
        Key.PATCH_REST_ARGS: {'title': 'New title'}
    },
}


def generate_test_cases():
    tc_list = []
    for name, test_case_params in LAYERS.items():
        for layer_by_server in base_test.LayerByUsedServers:
            all_params = deepcopy(test_case_params)
            name = f'{layer_by_server.publ_name_part}_{name}'
            test_case = base_test.TestCaseType(key=name,
                                               publication=Publication(workspace=WORKSPACE,
                                                                       type=process_client.LAYER_TYPE,
                                                                       name=name,
                                                                       ),
                                               type=EnumTestTypes.OPTIONAL,
                                               rest_args=layer_by_server.publication_definition.definition,
                                               params=all_params,
                                               marks=[pytest.mark.xfail(reason="Not yet implemented.")]
                                               if test_case_params.get('xfail') else []
                                               )
            tc_list.append(test_case)
    return tc_list


class TestLayer(base_test.TestSingleRestPublication):
    workspace = WORKSPACE

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = []

    test_cases = generate_test_cases()

    def test_layer(self, layer, rest_args, params):
        """Parametrized using pytest_generate_tests"""
        self.post_publication(layer, args=rest_args)

        assert_util.is_publication_valid_and_complete(layer)

        self.patch_publication(publication=layer,
                               args=params[Key.PATCH_REST_ARGS])

        assert_util.is_publication_valid_and_complete(layer)
        with app.app_context():
            publ_info = layman_util.get_publication_info(layer.workspace, layer.type, layer.name,
                                                         {'keys': params[Key.PATCH_REST_ARGS].keys()})
            for key, item in params[Key.PATCH_REST_ARGS].items():
                value = publ_info[key]
                assert value == item, f'key={key}, expected={item}, real={value}'
