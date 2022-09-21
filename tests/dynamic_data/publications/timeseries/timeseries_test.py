import os
import pytest

from test_tools import process_client
from tests import TestTypes, Publication
from tests.asserts.final.publication import util as assert_util, internal as assert_internal
from tests.dynamic_data import base_test

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests

DEFAULT_TIME_REGEXP = r'[0-9]{8}T[0-9]{9}Z(\?!.\*[0-9]{8}T[0-9]{9}Z.\*)'

LAYERS = {
    'default': {
        'params': {
            'time_regex': DEFAULT_TIME_REGEXP,
            'file_paths': ['sample/layman.layer/sample_tif_colortable_nodata.tif'],
        },
        'detail_values': {
            'exp_publication_detail': {
                'bounding_box': [868376.0, 522128.0, 940583.0, 593255.0],
                'native_crs': 'EPSG:3857',
                'native_bounding_box': [868376.0, 522128.0, 940583.0, 593255.0],
                'image_mosaic': True,
                '_file': {
                    'gdal_paths': ['/layman_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_default_post/input_file/sample_tif_colortable_nodata.tif'],
                    'path': '/layman_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_default_post/input_file/sample_tif_colortable_nodata.tif',
                    'normalized_file': {
                        'gs_paths': ['normalized_raster_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_default_post/sample_tif_colortable_nodata.tif'],
                        'paths': ['/geoserver/data_dir/normalized_raster_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_default_post/sample_tif_colortable_nodata.tif']
                    },
                },
                'file': {
                    'file_type': 'raster',
                    'path': 'layers/layer_default_post/input_file/sample_tif_colortable_nodata.tif',
                },
            },
            'file_extension': 'tif',
            'publ_type_detail': ('raster', 'sld'),
        },
    },
    'more_files_zip': {
        'params': {
            'time_regex': r'[0-9]{8}',
            'file_paths': [os.path.join(DIRECTORY, 'timeseries_tif.zip')],
        },
        'detail_values': {
            'exp_publication_detail': {
                'bounding_box': [1737105.4141226907, 6491458.724017749, 1765157.537707582, 6509901.824098258],
                'native_crs': 'EPSG:32633',
                'native_bounding_box': [543100.0, 5567910.0, 560930.0, 5579500.0],
                'image_mosaic': True,
                '_file': {
                    'gdal_paths': [
                        '/vsizip//layman_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_zip_post/input_file/timeseries_tif.zip/timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                        '/vsizip//layman_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_zip_post/input_file/timeseries_tif.zip/timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.tif',
                    ],
                    'path': '/layman_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_zip_post/input_file/timeseries_tif.zip/timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                    'normalized_file': {
                        'gs_paths': [
                            'normalized_raster_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_zip_post/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                            'normalized_raster_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_zip_post/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.tif',
                        ],
                        'paths': [
                            '/geoserver/data_dir/normalized_raster_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_zip_post/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                            '/geoserver/data_dir/normalized_raster_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_zip_post/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.tif',
                        ]
                    },
                },
                'file': {
                    'path': 'layers/layer_more_files_zip_post/input_file/timeseries_tif.zip/timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                },
            },
            'publ_type_detail': ('raster', 'sld'),
            'file_extension': 'zip/timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
            'gdal_prefix': '/vsizip/',
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
                '_file': {
                    'gdal_paths': [
                        '/layman_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_post/input_file/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                        '/layman_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_post/input_file/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.tif',
                    ],
                    'path': '/layman_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_post/input_file/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                    'normalized_file': {
                        'gs_paths': [
                            'normalized_raster_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_post/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                            'normalized_raster_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_post/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.tif',
                        ],
                        'paths': [
                            '/geoserver/data_dir/normalized_raster_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_post/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                            '/geoserver/data_dir/normalized_raster_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_post/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.tif',
                        ]
                    },
                },
                'file': {
                    'path': 'layers/layer_more_files_post/input_file/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                },
            },
            'publ_type_detail': ('raster', 'sld'),
            'file_extension': 'tif',
        },
    },
    'more_files_zip_chunk': {
        'params': {
            'time_regex': r'[0-9]{8}',
            'file_paths': [os.path.join(DIRECTORY, 'timeseries_tif.zip')],
            'with_chunks': True,
        },
        'detail_values': {
            'exp_publication_detail': {
                'bounding_box': [1737105.4141226907, 6491458.724017749, 1765157.537707582, 6509901.824098258],
                'native_crs': 'EPSG:32633',
                'native_bounding_box': [543100.0, 5567910.0, 560930.0, 5579500.0],
                'image_mosaic': True,
                '_file': {
                    'gdal_paths': [
                        '/vsizip//layman_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_zip_chunk_post/input_file/timeseries_tif.zip/timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                        '/vsizip//layman_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_zip_chunk_post/input_file/timeseries_tif.zip/timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.tif',
                    ],
                    'path': '/layman_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_zip_chunk_post/input_file/timeseries_tif.zip/timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                    'normalized_file': {
                        'gs_paths': [
                            'normalized_raster_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_zip_chunk_post/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                            'normalized_raster_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_zip_chunk_post/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.tif',
                        ],
                        'paths': [
                            '/geoserver/data_dir/normalized_raster_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_zip_chunk_post/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                            '/geoserver/data_dir/normalized_raster_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_zip_chunk_post/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.tif',
                        ]
                    },
                },
                'file': {
                    'path': 'layers/layer_more_files_zip_chunk_post/input_file/timeseries_tif.zip/timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                },
            },
            'publ_type_detail': ('raster', 'sld'),
            'file_extension': 'zip/timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
            'gdal_prefix': '/vsizip/',
        },
    },
    'more_files_chunks': {
        'params': {
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif'),
                os.path.join(DIRECTORY, 'timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.tif'),
            ],
            'with_chunks': True,
        },
        'detail_values': {
            'exp_publication_detail': {
                'bounding_box': [1737105.4141226907, 6491458.724017749, 1765157.537707582, 6509901.824098258],
                'native_crs': 'EPSG:32633',
                'native_bounding_box': [543100.0, 5567910.0, 560930.0, 5579500.0],
                'image_mosaic': True,
                '_file': {
                    'gdal_paths': [
                        '/layman_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_chunks_post/input_file/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                        '/layman_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_chunks_post/input_file/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.tif',
                    ],
                    'path': '/layman_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_chunks_post/input_file/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                    'normalized_file': {
                        'gs_paths': [
                            'normalized_raster_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_chunks_post/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                            'normalized_raster_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_chunks_post/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.tif',
                        ],
                        'paths': [
                            '/geoserver/data_dir/normalized_raster_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_chunks_post/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                            '/geoserver/data_dir/normalized_raster_data_test/workspaces/dynamic_test_workspace_timeseries_layer/layers/layer_more_files_chunks_post/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.tif',
                        ]
                    },
                },
                'file': {
                    'path': 'layers/layer_more_files_chunks_post/input_file/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                },
            },
            'publ_type_detail': ('raster', 'sld'),
            'file_extension': 'tif',
        },
    },
}


class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_workspace_timeseries_layer'

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = {
        'method': [
            base_test.RestMethodType('post_publication', 'post'),
        ],
    }

    test_cases = [base_test.TestCaseType(key=name,
                                         type=TestTypes.MANDATORY,
                                         params=test_case_params,
                                         marks=[pytest.mark.xfail(reason="Not yet implemented.")]
                                         if test_case_params.get('xfail') else []
                                         ) for name, test_case_params in LAYERS.items()]

    # pylint: disable=unused-argument
    @staticmethod
    def test_timeseries_layer(layer: Publication, key, params, rest_method):
        """Parametrized using pytest_generate_tests"""
        rest_method(layer, params=params.get('params', {}))

        assert_util.is_publication_valid_and_complete(layer)

        assert_internal.correct_values_in_detail(layer.workspace, layer.type, layer.name,
                                                 **params.get('detail_values', {}),
                                                 )
