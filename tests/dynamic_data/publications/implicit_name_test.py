from copy import deepcopy
import os
import pytest

from test_tools import process_client, external_db
from tests import EnumTestTypes, Publication4Test
from tests.asserts.final.publication import util as asserts_util
from tests.dynamic_data import base_test, base_test_classes

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests


class CompressDomain(base_test.CompressDomainBase):
    FALSE = (False, None)
    TRUE = (True, 'zipped', {
        'compress_settings': process_client.CompressTypeDef(archive_name='data_zip'),
    })


INPUT_FILE_PATH = 'sample/layman.layer/small_layer.geojson'
EXTERNAL_DB_TABLE = '_small_LAYER'
EXTERNAL_DB_SCHEMA = 'public'

PUBLICATIONS = {
    'one_data_file': {
        'publication_type': process_client.LAYER_TYPE,
        'expected_name': 'ne_110m_admin_0_countries',
        'rest_args': {
            'do_not_post_name': True,
            'file_paths': [
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
            ],
        },
        'mandatory_cases': {
            frozenset([CompressDomain.TRUE, base_test.WithChunksDomain, ]),
        },
        'specific_params': {
            frozenset([CompressDomain.TRUE, base_test.WithChunksDomain.TRUE, ]): {
                'expected_name': 'data_zip',
            },
        },
    },
    'timeseries_multi_file': {
        'publication_type': process_client.LAYER_TYPE,
        'expected_name': 's2a_msil2a_20220316t100031_n0400_r122_t33uwr_20220316t134748_tci_10m',
        'rest_args': {
            'do_not_post_name': True,
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                os.path.join(DIRECTORY, 'layer_timeseries',
                             'timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.TIF'),
                os.path.join(DIRECTORY, 'layer_timeseries',
                             'timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif'),
            ],
        },
        'mandatory_cases': {
            frozenset([CompressDomain.FALSE, base_test.WithChunksDomain.FALSE, ]),
        },
        'specific_params': {
            frozenset([CompressDomain.TRUE, base_test.WithChunksDomain.TRUE, ]): {
                'expected_name': 'data_zip',
            },
        },
        'ignored_cases': {
            frozenset([CompressDomain.FALSE, base_test.WithChunksDomain.TRUE, ]),
        },
    },
    'external_table': {
        'publication_type': process_client.LAYER_TYPE,
        'expected_name': 'small_layer',
        'rest_args': {
            'do_not_post_name': True,
            'external_table_uri': f"{external_db.URI_STR}?schema={EXTERNAL_DB_SCHEMA}&table={EXTERNAL_DB_TABLE}&geo_column=wkb_geometry",
        },
        'mandatory_cases': {
            frozenset([CompressDomain.FALSE, base_test.WithChunksDomain.FALSE, ]),
        },
        'specific_params': {},
        'ignored_cases': {
            frozenset([CompressDomain.FALSE, base_test.WithChunksDomain.TRUE, ]),
            frozenset([CompressDomain.TRUE, base_test.WithChunksDomain, ]),
        },
    },
}


def generate_test_cases():
    tc_list = []
    for name, test_case_params in PUBLICATIONS.items():
        all_params = deepcopy(test_case_params)
        rest_args = all_params.pop('rest_args')
        specific_types = {tc: EnumTestTypes.MANDATORY for tc in all_params.pop('mandatory_cases')}
        for case in all_params.pop('ignored_cases', {}):
            assert case not in specific_types
            specific_types[case] = EnumTestTypes.IGNORE
        specific_params = all_params.pop('specific_params')
        test_case = base_test.TestCaseType(key=name,
                                           publication=lambda params, cls: Publication4Test(
                                               workspace=cls.workspace,
                                               type=params['publication_type'],
                                               name=params['expected_name']),
                                           type=EnumTestTypes.OPTIONAL,
                                           specific_types=specific_types,
                                           rest_args=rest_args,
                                           params=all_params,
                                           specific_params=specific_params,
                                           marks=[pytest.mark.xfail(reason="Not yet implemented.")]
                                           if test_case_params.get('xfail') else []
                                           )
        tc_list.append(test_case)
    return tc_list


@pytest.mark.usefixtures('ensure_external_db')
class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_implicit_name'

    publication_type = None

    rest_parametrization = [
        base_test.WithChunksDomain,
        CompressDomain,
    ]

    test_cases = generate_test_cases()

    external_tables_to_create = [base_test_classes.ExternalTableDef(file_path=INPUT_FILE_PATH,
                                                                    db_schema=EXTERNAL_DB_SCHEMA,
                                                                    db_table=EXTERNAL_DB_TABLE,
                                                                    )]

    @staticmethod
    def test_implicit_name(publication: Publication4Test, rest_method, rest_args):
        """Parametrized using pytest_generate_tests"""
        rest_method.fn(publication, args=rest_args)

        asserts_util.is_publication_valid_and_complete(publication)
