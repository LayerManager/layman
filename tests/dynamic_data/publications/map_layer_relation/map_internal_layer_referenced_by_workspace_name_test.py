import os
import pytest

from layman import LaymanError
from test_tools import process_client
from tests import EnumTestTypes, Publication4Test
from tests.dynamic_data import base_test, base_test_classes


DIRECTORY = os.path.dirname(os.path.abspath(__file__))


WORKSPACE = 'test_map_internal_layer_by_ws_name'
INTERNAL_LAYER = Publication4Test(WORKSPACE, process_client.LAYER_TYPE, 'internal_layer', uuid='a0939eb1-3c48-4ad6-949e-0a170419ba90')


TEST_CASES = {
    'one_internal_layer': {
        'file_path': os.path.join(DIRECTORY, 'map_internal_layer_referenced_by_workspace_name.json'),
        'exp_wrongly_referenced_layers': [{
            'layer_index': 1,
            'workspace': f'{INTERNAL_LAYER.workspace}_wms',
            'layer_name': INTERNAL_LAYER.name,
        }],
    },
}

pytest_generate_tests = base_test.pytest_generate_tests


class TestPublication(base_test.TestSingleRestPublication):
    workspace = WORKSPACE
    publication_type = process_client.MAP_TYPE

    rest_parametrization = [
        base_test_classes.RestMethod
    ]

    test_cases = [base_test.TestCaseType(key=key,
                                         type=EnumTestTypes.OPTIONAL,
                                         rest_args={
                                             'file_paths': [params['file_path']]
                                         },
                                         params=params,
                                         specific_types={
                                             (base_test_classes.RestMethod.POST, ): EnumTestTypes.MANDATORY
                                         }
                                         ) for key, params in TEST_CASES.items()]

    def before_class(self):
        self.post_publication(INTERNAL_LAYER, scope='class')

    def test_publication(self, map, rest_method, rest_args, params):
        with pytest.raises(LaymanError) as exc_info:
            rest_method.fn(map, args=rest_args)
        assert exc_info.value.code == 59
        assert exc_info.value.data['wrongly_referenced_layers'] == params['exp_wrongly_referenced_layers']
