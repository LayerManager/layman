import os
import pytest

from test_tools import process_client
from tests import EnumTestTypes, Publication
from tests.asserts.final.publication import util as asserts_util
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

PUBLICATIONS = {
    'ne_110m_admin_0_countries': {
        'publication_type': process_client.LAYER_TYPE,
        'params': {
            'file_paths': [
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
            ],
        },
    },
    's2a_msil2a_20220316t100031_n0400_r122_t33uwr_20220316t134748_tci_10m': {
        'publication_type': process_client.LAYER_TYPE,
        'params': {
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                os.path.join(DIRECTORY, 'timeseries',
                             'timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif'),
                os.path.join(DIRECTORY, 'timeseries',
                             'timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.tif'),
            ],
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

    test_cases = [base_test.TestCaseType(key=name,
                                         publication=Publication(workspace='dynamic_test_workspace_implicit_name',
                                                                 type=params['publication_type'],
                                                                 name=name),
                                         type=EnumTestTypes.MANDATORY,
                                         params=params,
                                         marks=[pytest.mark.xfail(reason="Not yet implemented.")]
                                         if params.get('xfail') else []
                                         ) for name, params in PUBLICATIONS.items()]

    # pylint: disable=unused-argument
    @staticmethod
    def test_timeseries_layer(publication: Publication, key, params, rest_method):
        """Parametrized using pytest_generate_tests"""
        rest_method(publication, params={**params.get('params', {}),
                                         'do_not_post_name': True,
                                         })

        asserts_util.is_publication_valid_and_complete(publication)
