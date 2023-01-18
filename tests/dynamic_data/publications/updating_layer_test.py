import os

from test_tools import process_client
from tests import EnumTestTypes
from tests.asserts.final import publication as asserts_publ
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests


class TestUpdatingLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_updating_publication'

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = [
        base_test.RestMethod,
    ]

    test_cases = [base_test.TestCaseType(key='updating_layer',
                                         type=EnumTestTypes.MANDATORY,
                                         params={'compress': True,
                                                 'with_chunks': True,
                                                 'do_not_upload_chunks': True,
                                                 }
                                         )]

    @staticmethod
    def test_layer(layer, params, rest_method):
        """Parametrized using pytest_generate_tests"""
        rest_method(layer, args=params)

        exp_publication_detail = {
            '_file_type': 'unknown',
            '_style_type': 'sld',
            'native_bounding_box': [
                None,
                None,
                None,
                None
            ],
            'native_crs': None,
            'access_rights': {
                'read': [
                    'EVERYONE'
                ],
                'write': [
                    'EVERYONE'
                ]
            },
            'bounding_box': [
                None,
                None,
                None,
                None
            ],
            'file': {
                'file_type': 'unknown'
            },
            '_table_uri': None,
        }

        asserts_publ.internal.correct_values_in_detail(layer.workspace, layer.type, layer.name,
                                                       exp_publication_detail=exp_publication_detail,
                                                       publ_type_detail=('vector', 'sld'),
                                                       full_comparison=False,
                                                       file_extension=None,
                                                       keys_to_remove=['thumbnail', '_thumbnail', 'metadata', 'style', 'wms', '_wms',
                                                                       'description', 'wfs', 'db_table', ]
                                                       )
