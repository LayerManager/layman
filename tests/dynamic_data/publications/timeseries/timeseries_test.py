import os
import pytest

import crs as crs_def
from test_tools import process_client
from tests import TestTypes, Publication
from tests.asserts.final import publication as asserts_publ
from tests.asserts.final.publication import util as asserts_util
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

LAYERS = {
    'more_files_zip': {
        'params': {
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif'),
                os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.tif'),
            ],
            'compress': True,
            'compress_settings': process_client.CompressTypeDef(archive_name='timeseries_tif',
                                                                inner_directory='/timeseries_tif/',
                                                                file_name=None,
                                                                ),
        },
        'detail_values': {
            'exp_publication_detail': {
                'bounding_box': [1737105.4141226907, 6491458.724017749, 1765157.537707582, 6509901.824098258],
                'native_crs': 'EPSG:32633',
                'native_bounding_box': [543100.0, 5567910.0, 560930.0, 5579500.0],
                'image_mosaic': True,
                'wms': {
                    'time': {'default': '2022-03-19T00:00:00Z',
                             'units': 'ISO8601',
                             'values': ['2022-03-16T00:00:00.000Z',
                                        '2022-03-19T00:00:00.000Z']},
                },
            },
            'publ_type_detail': ('raster', 'sld'),
            'gdal_prefix': '/vsizip/',
            'files': [
                'timeseries_tif.zip/timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                'timeseries_tif.zip/timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.tif',
            ]
        },
    },
    'more_files': {
        'params': {
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif'),
                os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.tif'),
            ],
        },
        'detail_values': {
            'exp_publication_detail': {
                'bounding_box': [1737105.4141226907, 6491458.724017749, 1765157.537707582, 6509901.824098258],
                'native_crs': 'EPSG:32633',
                'native_bounding_box': [543100.0, 5567910.0, 560930.0, 5579500.0],
                'image_mosaic': True,
                'wms': {
                    'time': {'default': '2022-03-19T00:00:00Z',
                             'units': 'ISO8601',
                             'values': ['2022-03-16T00:00:00.000Z',
                                        '2022-03-19T00:00:00.000Z']},
                },
            },
            'publ_type_detail': ('raster', 'sld'),
            'files': [
                'S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                'S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.tif',
            ]
        },
    },
}


def generate_test_cases():
    tc_list = list()
    for name, test_case_params in LAYERS.items():
        for name_suffix, with_chunks_value in [('', False),
                                               ('_chunks', True),
                                               ]:
            params = test_case_params
            params['params']['with_chunks'] = with_chunks_value
            test_case = base_test.TestCaseType(key=name + name_suffix,
                                               type=TestTypes.MANDATORY,
                                               params=params,
                                               marks=[pytest.mark.xfail(reason="Not yet implemented.")]
                                               if test_case_params.get('xfail') else []
                                               )
            tc_list.append(test_case)
    return tc_list


class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_timeseries_layer'

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = {
        'method': [
            base_test.RestMethodType('post_publication', 'post'),
        ],
    }

    test_cases = generate_test_cases()

    # pylint: disable=unused-argument
    @staticmethod
    def test_timeseries_layer(layer: Publication, key, params, rest_method):
        """Parametrized using pytest_generate_tests"""
        rest_method(layer, params=params.get('params', {}))

        asserts_util.is_publication_valid_and_complete(layer)

        asserts_publ.internal.correct_values_in_detail(layer.workspace, layer.type, layer.name,
                                                       **params.get('detail_values', {}),
                                                       )

        for time in [
            '2022-03-16',
            '2022-03-19',
        ]:
            exp_wms = os.path.join(DIRECTORY, f"wms_{time}.png")
            asserts_publ.geoserver.wms_spatial_precision(layer.workspace, layer.type, layer.name, crs=crs_def.EPSG_3857,
                                                         extent=[1743913.19942603237, 6499107.284021802247, 1755465.937341974815, 6503948.597792930901, ],
                                                         img_size=(1322, 554),
                                                         wms_version='1.3.0',
                                                         pixel_diff_limit=200,
                                                         obtained_file_path=f'tmp/artifacts/test_timeseries/downloaded_wms_{layer.name}_{time}.png',
                                                         expected_file_path=exp_wms,
                                                         time=time,
                                                         )

        exp_wms = os.path.join(DIRECTORY, f"wms_2022-03-19.png")
        asserts_publ.geoserver.wms_spatial_precision(layer.workspace, layer.type, layer.name, crs=crs_def.EPSG_3857,
                                                     extent=[1743913.19942603237, 6499107.284021802247, 1755465.937341974815, 6503948.597792930901, ],
                                                     img_size=(1322, 554),
                                                     wms_version='1.3.0',
                                                     pixel_diff_limit=200,
                                                     obtained_file_path=f'tmp/artifacts/test_timeseries/downloaded_wms_{layer.name}_{time}.png',
                                                     expected_file_path=exp_wms,
                                                     )
        exp_thumbnail = os.path.join(DIRECTORY, f"thumbnail_timeseries.png")
        asserts_publ.internal.thumbnail_equals(layer.workspace, layer.type, layer.name, exp_thumbnail, max_diffs=1)
