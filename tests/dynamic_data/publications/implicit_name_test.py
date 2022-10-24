import os
import pytest

from test_tools import process_client
from tests import EnumTestTypes, Publication
from tests.asserts.final.publication import util as asserts_util
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

PUBLICATIONS = {
    'one_data_file': {
        'publication_type': process_client.LAYER_TYPE,
        'expected_name': 'ne_110m_admin_0_countries',
        'params': {
            'file_paths': [
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
            ],
        },
    },
    'one_data_file_with_chunks': {
        'publication_type': process_client.LAYER_TYPE,
        'expected_name': 'small_layer',
        'params': {
            'file_paths': ['sample/layman.layer/small_layer.geojson'],
            'with_chunks': True,
        },
    },
    'one_data_file_compressed': {
        'publication_type': process_client.LAYER_TYPE,
        'expected_name': 'small_layer_with_id',
        'params': {
            'file_paths': ['sample/layman.layer/small_layer_with_id.geojson'],
            'compress': True,
            'compress_settings': process_client.CompressTypeDef(archive_name='small_layer_with_id'),
        },
    },
    'one_data_file_compressed_with_chunks': {
        'publication_type': process_client.LAYER_TYPE,
        'expected_name': 'small_zip_layer',
        'params': {
            'file_paths': ['sample/layman.layer/small_layer.geojson'],
            'compress': True,
            'compress_settings': process_client.CompressTypeDef(archive_name='small_zip_layer'),
            'with_chunks': True,
        },
    },
    'timeseries_multi_file': {
        'publication_type': process_client.LAYER_TYPE,
        'expected_name': 's2a_msil2a_20220316t100031_n0400_r122_t33uwr_20220316t134748_tci_10m',
        'params': {
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                os.path.join(DIRECTORY, 'timeseries',
                             'timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.TIF'),
                os.path.join(DIRECTORY, 'timeseries',
                             'timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif'),
            ],
        },
    },
    'timeseries_compressed_with_chunks': {
        'publication_type': process_client.LAYER_TYPE,
        'expected_name': 'timeseries_tif',
        'params': {
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                os.path.join(DIRECTORY, 'timeseries',
                             'timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.TIF'),
                os.path.join(DIRECTORY, 'timeseries',
                             'timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif'),
            ],
            'compress': True,
            'compress_settings': process_client.CompressTypeDef(archive_name='timeseries_tif',
                                                                inner_directory='/timeseries_tif/',
                                                                file_name=None,
                                                                ),
            'with_chunks': True,
        },
    },
    'timeseries_compressed': {
        'publication_type': process_client.LAYER_TYPE,
        'expected_name': 's2a_msil2a_20220319t100731_n0400_r022_t33uwr_20220319t131812_tci_10m',
        'params': {
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                os.path.join(DIRECTORY, 'timeseries',
                             'timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.TIF'),
            ],
            'compress': True,
            'compress_settings': process_client.CompressTypeDef(archive_name='timeseries_tif',
                                                                inner_directory='/timeseries_tif/',
                                                                file_name=None,
                                                                ),
        },
    },
}


class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_implicit_name'

    publication_type = None

    rest_parametrization = {
        'method': [
            base_test.RestMethodType('post_publication', 'post'),
        ],
    }

    test_cases = [base_test.TestCaseType(pytest_id=key,
                                         key=key,
                                         publication=Publication(workspace='dynamic_test_workspace_implicit_name',
                                                                 type=params['publication_type'],
                                                                 name=params['expected_name']),
                                         type=EnumTestTypes.MANDATORY,
                                         params=params,
                                         marks=[pytest.mark.xfail(reason="Not yet implemented.")]
                                         if params.get('xfail') else []
                                         ) for key, params in PUBLICATIONS.items()]

    # pylint: disable=unused-argument
    @staticmethod
    def test_implicit_name(publication: Publication, key, params, rest_method):
        """Parametrized using pytest_generate_tests"""
        rest_method(publication, params={**params.get('params', {}),
                                         'do_not_post_name': True,
                                         })

        asserts_util.is_publication_valid_and_complete(publication)
