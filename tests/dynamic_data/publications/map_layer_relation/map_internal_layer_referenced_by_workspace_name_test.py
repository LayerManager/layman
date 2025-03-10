import os
import pytest

from layman import LaymanError
from test_tools import process_client
from tests import EnumTestTypes, Publication4Test
from tests.dynamic_data import base_test, base_test_classes


DIRECTORY = os.path.dirname(os.path.abspath(__file__))


WORKSPACE = 'test_map_internal_layer_by_ws_name'
INTERNAL_LAYER = Publication4Test(WORKSPACE, process_client.LAYER_TYPE, 'internal_layer', uuid='a0939eb1-3c48-4ad6-949e-0a170419ba90')
INTERNAL_LAYER_2 = Publication4Test(WORKSPACE, process_client.LAYER_TYPE, 'internal_layer_2', uuid='bf83565c-46fb-4d37-8eb1-2dad9c86a8d0')


TEST_CASES = {
    'one_internal_layer': {
        'file_path': os.path.join(DIRECTORY, 'map_internal_layer_referenced_by_workspace_name.json'),
        'exp_wrongly_referenced_layers': [{
            'layer_index': 1,
            'workspace': f'{INTERNAL_LAYER.workspace}_wms',
            'layer_name': INTERNAL_LAYER.name,
        }],
        'mandatory_cases': {
            frozenset([base_test.RestMethod.POST]),
        },
        'ignore_cases': {},
    },
    'more_internal_layers': {
        'file_path': os.path.join(DIRECTORY, 'map_more_internal_layers_referenced_by_workspace_name.json'),
        'exp_wrongly_referenced_layers': [{
            'layer_index': 1,
            'workspace': f'{INTERNAL_LAYER.workspace}_wms',
            'layer_name': INTERNAL_LAYER.name,
        }, {
            'layer_index': 2,
            'workspace': f'{INTERNAL_LAYER.workspace}_wms',
            'layer_name': INTERNAL_LAYER_2.name,
        }, {
            'layer_index': 3,
            'workspace': f'{INTERNAL_LAYER.workspace}',
            'layer_name': INTERNAL_LAYER.name,
        }, {
            'layer_index': 3,
            'workspace': f'{INTERNAL_LAYER.workspace}',
            'layer_name': INTERNAL_LAYER_2.name,
        }, {
            'layer_index': 4,
            'workspace': f'{INTERNAL_LAYER.workspace}',
            'layer_name': INTERNAL_LAYER.name,
        }, {
            'layer_index': 4,
            'workspace': f'{INTERNAL_LAYER.workspace}',
            'layer_name': INTERNAL_LAYER_2.name,
        },
        ],
        'mandatory_cases': {},
        'ignore_cases': {},
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
                                             **{
                                                 case: EnumTestTypes.IGNORE
                                                 for case in params['ignore_cases']
                                             },
                                             **{
                                                 case: EnumTestTypes.MANDATORY
                                                 for case in params['mandatory_cases']
                                             },
                                         },
                                         ) for key, params in TEST_CASES.items()]

    def before_class(self):
        self.post_publication(INTERNAL_LAYER, scope='class')
        self.post_publication(INTERNAL_LAYER_2, scope='class')

    def test_publication(self, map, rest_method, rest_args, params):
        with pytest.raises(LaymanError) as exc_info:
            rest_method.fn(map, args=rest_args)
        assert exc_info.value.code == 59
        assert exc_info.value.data['wrongly_referenced_layers'] == params['exp_wrongly_referenced_layers']
