import copy
import os
import logging

from layman import LaymanError, settings
from layman.layer.util import EXTERNAL_TABLE_URI_PATTERN
from tests.asserts import util as asserts_util
from tests.asserts import processing
from tests.asserts.final import publication
from test_tools import process_client, util
from .. import common_publications as publications
from .... import Action, Publication, dynamic_data as consts, EnumTestTypes, EnumTestKeys

KEY_PUBLICATION_TYPE = 'publ_type'
KEY_ACTION_PARAMS = 'action_params'
KEY_EXPECTED_EXCEPTION = 'expected_exception'
KEY_DEFAULT = 'default'
KEY_PATCHES = 'patches'
KEY_PATCH_POST = 'post_params'
KEY_SKIP_POST = 'skip_post'
KEY_ONLY_FIRST_PARAMETRIZATION = 'only_first_parametrization'
KEY_FAILED_INFO_KEY = 'failed_info_key'

DIRECTORY = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)

REST_PARAMETRIZATION = {
    'with_chunks': {False: '', True: 'chunks'},
    'compress': {False: '', True: 'zipped'},
}

TESTCASES = {
    'vector_time_regex': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'time_regex': r'[0-9]{8}T[0-9]{6}Z(\?!.\*[0-9]{8}T[0-9]{6}Z.\*)',
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 48,
                          'data': 'Vector layers are not allowed to be combined with `time_regex` parameter.',
                          },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
            },
        },
    },
    'raster_vector_time_regex': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'time_regex': r'[0-9]{8}T[0-9]{6}Z(\?!.\*[0-9]{8}T[0-9]{6}Z.\*)',
            'file_paths': ['sample/layman.layer/sample_jp2_rgb.jp2',
                           'sample/layman.layer/single_point.dbf',
                           'sample/layman.layer/single_point.prj',
                           'sample/layman.layer/single_point.shp',
                           'sample/layman.layer/single_point.shx',
                           'sample/layman.layer/single_point.qpj',
                           ],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'data': {'expected': 'All main files with the same extension.',
                                   'files': ['sample_jp2_rgb.jp2', 'single_point.shp'],
                                   'extensions': ['.jp2', '.shp'],
                                   'parameter': 'file',
                                   },
                          },
            frozenset([('compress', True), ('with_chunks', False)]): {
                'data': {'files': ['temporary_zip_file.zip/sample_jp2_rgb.jp2', 'temporary_zip_file.zip/single_point.shp'],
                         },
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
                'data': {'files': ['raster_vector_time_regex_post_chunks_zipped.zip/sample_jp2_rgb.jp2', 'raster_vector_time_regex_post_chunks_zipped.zip/single_point.shp'],
                         },
            },
        },
    },
    'dif_raster_types_time_regex': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'time_regex': r'[0-9]{8}T[0-9]{6}Z(\?!.\*[0-9]{8}T[0-9]{6}Z.\*)',
            'file_paths': ['sample/layman.layer/sample_jp2_j2w_rgb.j2w',
                           'sample/layman.layer/sample_jp2_j2w_rgb.jp2',
                           'sample/layman.layer/sample_jpeg_jgw_rgb.jgw',
                           'sample/layman.layer/sample_jpeg_jgw_rgb.jpeg',
                           ],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'data': {'expected': 'All main files with the same extension.',
                                   'files': ['sample_jp2_j2w_rgb.jp2', 'sample_jpeg_jgw_rgb.jpeg', ],
                                   'extensions': ['.jp2', '.jpeg'],
                                   'parameter': 'file',
                                   },
                          },
            frozenset([('compress', True), ('with_chunks', False)]): {
                'data': {'files': ['temporary_zip_file.zip/sample_jp2_j2w_rgb.jp2', 'temporary_zip_file.zip/sample_jpeg_jgw_rgb.jpeg', ],
                         },
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
                'data': {'files': ['dif_raster_types_time_regex_post_chunks_zipped.zip/sample_jp2_j2w_rgb.jp2', 'dif_raster_types_time_regex_post_chunks_zipped.zip/sample_jpeg_jgw_rgb.jpeg', ],
                         },
            },
        },
    },
    'raster_and_zip_raster_time_regex': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'time_regex': r'[0-9]{8}T[0-9]{6}Z(\?!.\*[0-9]{8}T[0-9]{6}Z.\*)',
            'file_paths': ['sample/layman.layer/sample_jp2_rgb.jp2',
                           'sample/layman.layer/sample_jp2_rgb.zip',
                           ],
            'compress': False,
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'data': {'expected': 'One compressed file or one or more uncompressed files.',
                                   'files': ['sample_jp2_rgb.jp2', 'sample_jp2_rgb.zip', ],
                                   'parameter': 'file',
                                   },
                          },
        },
    },
    'different_rasters_time_regex': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'time_regex': r'cz_[0-9]{4}',
            'file_paths': ['tests/dynamic_data/publications/crs/rasters/cz_4326.tif',
                           'tests/dynamic_data/publications/crs/rasters/cz_32633.tif',
                           ],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'data': {'expected': 'All main files with the same CRS.',
                                   'crs': ['EPSG:32633', 'EPSG:4326', ],
                                   'parameter': 'file',
                                   },
                          },
            frozenset([('compress', False), ('with_chunks', True)]): {
                'sync': False,
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
            },
        },
    },
    'different_bands_rasters_time_regex': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'time_regex': r'[a-z]{5}',
            'file_paths': ['sample/layman.layer/sample_tif_rgba.tif',
                           'sample/layman.layer/sample_tif_rgb_nodata.tif',
                           ],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'data': {'expected': 'All main files with the same color interpretations.',
                                   'color_interpretations': [['Red', 'Green', 'Blue'], ['Red', 'Green', 'Blue', 'Alpha']],
                                   'parameter': 'file',
                                   },
                          },
            frozenset([('compress', False), ('with_chunks', True)]): {
                'sync': False,
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
            },
        },
    },
    'non_data_file_without_data_file': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': ['sample/layman.layer/sample_jp2_j2w_rgb.j2w'],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'message': 'Wrong parameter value',
                          'data': {
                              'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                              'files': ['sample_jp2_j2w_rgb.j2w'],
                              'message': 'No data file in input.',
                              'parameter': 'file',
                          }
                          },
            frozenset([('compress', True), ('with_chunks', False)]): {
                'data': {'files': ['temporary_zip_file.zip/sample_jp2_j2w_rgb.j2w'],
                         'message': 'Zip file without data file inside.', }
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
                'data': {'files': ['non_data_file_without_data_file_post_chunks_zipped.zip/sample_jp2_j2w_rgb.j2w'],
                         'message': 'Zip file without data file inside.', }
            },
        },
        KEY_PATCHES: {
            'full': {
                KEY_PATCH_POST: publications.SMALL_LAYER.definition,
                KEY_ACTION_PARAMS: {
                    'file_paths': ['sample/layman.layer/sample_jp2_j2w_rgb.j2w'],
                },
                KEY_EXPECTED_EXCEPTION: {
                    frozenset([('compress', True), ('with_chunks', True)]): {
                        'data': {'files': ['non_data_file_without_data_file_patch_full_chunks_zipped.zip/sample_jp2_j2w_rgb.j2w'],
                                 }
                    },
                },
            },
        },
    },
    'patch_with_time_regex_without_data_file': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_SKIP_POST: True,
        KEY_ACTION_PARAMS: {},
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 48,
                          'message': 'Wrong combination of parameters',
                          'data': 'Parameter time_regex is allowed only in combination with files.',
                          },
        },
        KEY_PATCHES: {
            'full': {
                KEY_PATCH_POST: {
                    'time_regex': r'[0-9]{8}',
                    'file_paths': [
                        'tests/dynamic_data/publications/layer_timeseries/timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                        'tests/dynamic_data/publications/layer_timeseries/timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.TIF',
                    ],
                },
                KEY_ACTION_PARAMS: {
                    'time_regex': r'[0-9]{8}T[0-9]{6}Z(\?!.\*[0-9]{8}T[0-9]{6}Z.\*)',
                    'compress': False,
                    'with_chunks': False,
                },
            },
        },
    },
    'time_regex_with_non_data_file': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'time_regex': r'[a-z]{5}',
            'file_paths': ['sample/layman.layer/sample_jp2_j2w_rgb.j2w'],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'message': 'Wrong parameter value',
                          'data': {
                              'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                              'files': ['sample_jp2_j2w_rgb.j2w'],
                              'message': 'No data file in input.',
                              'parameter': 'file',
                          }
                          },
            frozenset([('compress', True), ('with_chunks', False)]): {
                'data': {'files': ['temporary_zip_file.zip/sample_jp2_j2w_rgb.j2w'],
                         'message': 'Zip file without data file inside.', }
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
                'data': {'files': ['time_regex_with_non_data_file_post_chunks_zipped.zip/sample_jp2_j2w_rgb.j2w'],
                         'message': 'Zip file without data file inside.', }
            },
        },
        KEY_PATCHES: {
            'full': {
                KEY_PATCH_POST: publications.SMALL_LAYER.definition,
                KEY_ACTION_PARAMS: {
                    'time_regex': r'[0-9]{8}T[0-9]{6}Z(\?!.\*[0-9]{8}T[0-9]{6}Z.\*)',
                    'file_paths': ['sample/layman.layer/sample_jp2_j2w_rgb.j2w'],
                },
                KEY_EXPECTED_EXCEPTION: {
                    frozenset([('compress', True), ('with_chunks', True)]): {
                        'data': {'files': ['time_regex_with_non_data_file_patch_full_chunks_zipped.zip/sample_jp2_j2w_rgb.j2w'],
                                 }
                    },
                },
            },
        },
    },
    'too_long_filename_with_time_regexp': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                f'{DIRECTORY}/211_too_long_name_20220319_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.zip',
            ],
            'compress': False,
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 48,
                          'message': 'Wrong combination of parameters',
                          'data': {
                              'message': 'Too long filename in timeseries.',
                              'expected': 'All files names shorter than 211 characters',
                              'too_long_filenames': ['211_too_long_name_20220319_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.zip/211_too_long_name_20220319_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.tif'],
                          },
                          },
            frozenset([('compress', False), ('with_chunks', True)]): {
                'sync': False,
                'data': {'too_long_filenames': ['too_long_filename_with_time_regexp_post_chunks.zip/211_too_long_name_20220319_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.tif']}
            },
        },
        KEY_PATCHES: {
            'full': {
                KEY_PATCH_POST: {},
                KEY_ACTION_PARAMS: {
                    'time_regex': r'[0-9]{8}',
                    'file_paths': [
                        f'{DIRECTORY}/211_too_long_name_20220319_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.zip',
                    ],
                    'compress': False,
                },
                KEY_EXPECTED_EXCEPTION: {
                    frozenset([('compress', False), ('with_chunks', True)]): {
                        'data': {'too_long_filenames': ['too_long_filename_with_time_regexp_patch_full_chunks.zip/211_too_long_name_20220319_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.tif']}
                    },
                },
            },
        },
    },
    'unsafe_timeseries_filename_with_dot': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                f'{DIRECTORY}/.20220316.tif',
            ],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 48,
                          'message': 'Wrong combination of parameters',
                          'data': {
                              'message': 'Unsafe filename in timeseries.',
                              'expected': 'All slugified file names matching pattern ^(?![.])[a-zA-Z0-9_.-]+$',
                              'unsafe_slugified_filenames': ['.20220316.tif'],
                          },
                          },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
            },
        },
        KEY_PATCHES: {
            'full': {
                KEY_PATCH_POST: {},
                KEY_ACTION_PARAMS: {
                    'time_regex': r'[0-9]{8}',
                    'file_paths': [
                        f'{DIRECTORY}/.20220316.tif',
                    ],
                },
            },
        },
    },
    'unsafe_timeseries_filename_with_cyrillic': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                f'{DIRECTORY}/річка_20220316.tif',
            ],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 48,
                          'message': 'Wrong combination of parameters',
                          'data': {
                              'message': 'Unsafe filename in timeseries.',
                              'expected': 'All slugified file names matching pattern ^(?![.])[a-zA-Z0-9_.-]+$',
                              'unsafe_slugified_filenames': ['річка_20220316.tif'],
                          },
                          },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
            },
        },
        KEY_PATCHES: {
            'full': {
                KEY_PATCH_POST: {},
                KEY_ACTION_PARAMS: {
                    'time_regex': r'[0-9]{8}',
                    'file_paths': [
                        f'{DIRECTORY}/річка_20220316.tif',
                    ],
                },
            },
        },
    },
    'raster_wrong_crs': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [
                'tests/dynamic_data/publications/layer_timeseries/timeseries_tif/S2A_MSIL2A_20220316T100031.0.tif'
            ],
            'crs': 'EPSG:4326'
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_FAILED_INFO_KEY: 'wms',
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 500,
                          'sync': False,
                          'code': 53,
                          'message': 'Error when publishing on GeoServer. It happens for example for raster files with wrong explicit CRS.',
                          },
        },
    },
    'duplicate_filename_differs_in_case': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [
                f'{DIRECTORY}/small_layer.geojson',
                f'{DIRECTORY}/small_layer.README.txt',
                f'{DIRECTORY}/small_layer.readme.txt',
            ],
            'compress': False,
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'message': 'Wrong parameter value',
                          'data': {
                              'parameter': 'file',
                              'message': 'Two or more input file names map to the same name.',
                              'expected': 'Input file names that differ at least in one letter (ignoring case and diacritics) or number.',
                              'similar_filenames_mapping': {
                                  'small_layer.README.txt': 'duplicate_filename_differs_in_case_post.readme.txt',
                                  'small_layer.readme.txt': 'duplicate_filename_differs_in_case_post.readme.txt',
                              },
                          },
                          },
            frozenset([('compress', False), ('with_chunks', True)]): {
                'data': {
                    'similar_filenames_mapping': {
                        'small_layer.README.txt': 'duplicate_filename_differs_in_case_post_chunks.readme.txt',
                        'small_layer.readme.txt': 'duplicate_filename_differs_in_case_post_chunks.readme.txt',
                    },
                },
            },
        },
        KEY_PATCHES: {
            'full': {
                KEY_PATCH_POST: {},
                KEY_ACTION_PARAMS: {
                    'file_paths': [
                        f'{DIRECTORY}/small_layer.geojson',
                        f'{DIRECTORY}/small_layer.README.txt',
                        f'{DIRECTORY}/small_layer.readme.txt',
                    ],
                },
                KEY_EXPECTED_EXCEPTION: {
                    frozenset([('compress', False), ('with_chunks', False)]): {
                        'data': {
                            'similar_filenames_mapping': {
                                'small_layer.README.txt': 'duplicate_filename_differs_in_case_patch_full.readme.txt',
                                'small_layer.readme.txt': 'duplicate_filename_differs_in_case_patch_full.readme.txt',
                            },
                        },
                    },
                    frozenset([('compress', False), ('with_chunks', True)]): {
                        'data': {
                            'similar_filenames_mapping': {
                                'small_layer.README.txt': 'duplicate_filename_differs_in_case_patch_full_chunks.readme.txt',
                                'small_layer.readme.txt': 'duplicate_filename_differs_in_case_patch_full_chunks.readme.txt',
                            },
                        },
                    },
                },
            },
        },
    },
    'duplicate_filename_differs_in_diacritics': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                f'{DIRECTORY}/snimek_20220316.tif',
                f'{DIRECTORY}/snímek_20220316.tif',
            ],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'message': 'Wrong parameter value',
                          'data': {
                              'parameter': 'file',
                              'message': 'Two or more input file names map to the same name.',
                              'expected': 'Input file names that differ at least in one letter (ignoring case and diacritics) or number.',
                              'similar_filenames_mapping': {
                                  'snimek_20220316.tif': 'snimek_20220316.tif',
                                  'snímek_20220316.tif': 'snimek_20220316.tif',
                              },
                          },
                          },
            frozenset([('compress', True), ('with_chunks', False)]): {
                'data': {
                    'similar_filenames_mapping': {
                        asserts_util.KEY_REPLACE: True,
                        'temporary_zip_file.zip/snimek_20220316.tif': 'snimek_20220316.tif',
                        'temporary_zip_file.zip/snímek_20220316.tif': 'snimek_20220316.tif',
                    },
                },
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
                'data': {
                    'similar_filenames_mapping': {
                        asserts_util.KEY_REPLACE: True,
                        'duplicate_filename_differs_in_diacritics_post_chunks_zipped.zip/snimek_20220316.tif': 'snimek_20220316.tif',
                        'duplicate_filename_differs_in_diacritics_post_chunks_zipped.zip/snímek_20220316.tif': 'snimek_20220316.tif',
                    },
                },
            },
        },
        KEY_PATCHES: {
            'full': {
                KEY_PATCH_POST: {},
                KEY_ACTION_PARAMS: {
                    'time_regex': r'[0-9]{8}',
                    'file_paths': [
                        f'{DIRECTORY}/snimek_20220316.tif',
                        f'{DIRECTORY}/snímek_20220316.tif',
                    ],
                },
                KEY_EXPECTED_EXCEPTION: {
                    frozenset([('compress', True), ('with_chunks', False)]): {
                        'data': {
                            'similar_filenames_mapping': {
                                asserts_util.KEY_REPLACE: True,
                                'temporary_zip_file.zip/snimek_20220316.tif': 'snimek_20220316.tif',
                                'temporary_zip_file.zip/snímek_20220316.tif': 'snimek_20220316.tif',
                            },
                        },
                    },
                    frozenset([('compress', True), ('with_chunks', True)]): {
                        'sync': False,
                        'data': {
                            'similar_filenames_mapping': {
                                asserts_util.KEY_REPLACE: True,
                                'duplicate_filename_differs_in_diacritics_patch_full_chunks_zipped.zip/snimek_20220316.tif': 'snimek_20220316.tif',
                                'duplicate_filename_differs_in_diacritics_patch_full_chunks_zipped.zip/snímek_20220316.tif': 'snimek_20220316.tif',
                            },
                        },
                    },
                },
            },
        },
    },
    'none_file_none_external_table_uri': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_ACTION_PARAMS: {
            'file_paths': [],
            'external_table_uri': '',
            'compress': False,
            'with_chunks': False,
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 1,
                          'message': 'Missing parameter',
                          'data': {
                              'parameters': ['file', 'external_table_uri'],
                              'message': 'Both `file` and `external_table_uri` parameters are empty',
                              'expected': 'One of the parameters is filled.',
                          },
                          },
        },
    },
    'file_and_external_table_uri': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_ACTION_PARAMS: {
            'file_paths': ['sample/layman.layer/small_layer.geojson'],
            'external_table_uri': 'postgresql://username:password@host:port/dbname?table=table_name&geo_column=geo_column_name',
            'compress': False,
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 48,
                          'message': 'Wrong combination of parameters',
                          'data': {
                              'parameters': ['file', 'external_table_uri'],
                              'message': 'Both `file` and `external_table_uri` parameters are filled',
                              'expected': 'Only one of the parameters is fulfilled.',
                              'found': {
                                  'file': ['small_layer.geojson'],
                                  'external_table_uri': 'postgresql://username:password@host:port/dbname?table=table_name&geo_column=geo_column_name',
                              }},
                          },
        },
        KEY_PATCHES: {
            'full': {
                KEY_PATCH_POST: {},
            },
        },
    },
    'partial_external_table_uri': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_ACTION_PARAMS: {
            'external_table_uri': 'external_table_uri',
            'compress': False,
            'with_chunks': False,
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'message': 'Wrong parameter value',
                          'data': {'parameter': 'external_table_uri',
                                   'message': 'Parameter `external_table_uri` is expected to have URI scheme `postgresql`',
                                   'expected': EXTERNAL_TABLE_URI_PATTERN,
                                   'found': {
                                       'external_table_uri': 'external_table_uri',
                                       'uri_scheme': '',
                                   },
                                   },
                          },
        },
        KEY_PATCHES: {
            'full': {
                KEY_PATCH_POST: {},
            },
        },
    },
    'crs_and_external_table_uri': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_ACTION_PARAMS: {
            'crs': 'EPSG:4326',
            'external_table_uri': 'postgresql://username:password@host:port/dbname?table=table_name&geo_column=geo_column_name',
            'compress': False,
            'with_chunks': False,
            'skip_asserts': True,
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 48,
                          'message': 'Wrong combination of parameters',
                          'data': {
                              'parameters': ['crs', 'file'],
                              'message': 'Parameter `crs` needs also parameter `file`.',
                              'expected': 'Input files in `file` parameter or empty `crs` parameter.',
                              'found': {
                                  'crs': 'EPSG:4326',
                                  'file': [],
                              }},
                          },
        },
        KEY_PATCHES: {
            'full': {
                KEY_PATCH_POST: {},
            },
        },
    },
}

VALIDATION_PATCH_ACTION = {
    consts.KEY_ACTION: {
        consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
            'file_paths': ['sample/layman.layer/small_layer.geojson'],
            'style_file': 'sample/style/basic.sld',
        }),
        consts.KEY_RESPONSE_ASSERTS: [
            Action(processing.response.valid_post, {}),
        ],
    },
    consts.KEY_FINAL_ASSERTS: [
        *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
        Action(publication.internal.correct_values_in_detail, publications.SMALL_LAYER.info_values),
        Action(publication.internal.thumbnail_equals, {
            'exp_thumbnail': publications.SMALL_LAYER.thumbnail,
        }),
    ],
}


def generate(workspace=None):
    workspace = workspace or consts.COMMON_WORKSPACE
    test_type_str = os.getenv(EnumTestKeys.TYPE.value) or EnumTestTypes.MANDATORY.value
    test_type = EnumTestTypes(test_type_str)
    default_only_first_parametrization = test_type != EnumTestTypes.OPTIONAL

    result = {}
    for testcase, tc_params in TESTCASES.items():
        if test_type == EnumTestTypes.MANDATORY:
            if tc_params.get(EnumTestKeys.TYPE, EnumTestTypes.MANDATORY) == EnumTestTypes.OPTIONAL:
                continue

        failed_info_key = tc_params.get(KEY_FAILED_INFO_KEY, 'file')
        assert_no_bbox_and_crs = KEY_FAILED_INFO_KEY not in tc_params
        if not tc_params.get(KEY_SKIP_POST, False):
            action_parametrization = util.get_test_case_parametrization(param_parametrization=REST_PARAMETRIZATION,
                                                                        only_first_parametrization=default_only_first_parametrization,
                                                                        default_params=tc_params[KEY_ACTION_PARAMS],
                                                                        action_parametrization=[('', None, []), ],
                                                                        )
            for test_case_postfix, _, _, rest_param_dict in action_parametrization:
                rest_param_frozen_set = frozenset(rest_param_dict.items())
                default_exp_exception = copy.deepcopy(tc_params[KEY_EXPECTED_EXCEPTION][KEY_DEFAULT])
                exception_diff = tc_params[KEY_EXPECTED_EXCEPTION].get(rest_param_frozen_set, {})
                exp_exception = asserts_util.recursive_dict_update(default_exp_exception, copy.deepcopy(exception_diff))
                is_sync = exp_exception.pop('sync')
                if is_sync:
                    action_def = {
                        consts.KEY_ACTION: {
                            consts.KEY_CALL: Action(process_client.publish_workspace_publication,
                                                    {**tc_params[KEY_ACTION_PARAMS],
                                                     **rest_param_dict}),
                            consts.KEY_CALL_EXCEPTION: {
                                consts.KEY_EXCEPTION: LaymanError,
                                consts.KEY_EXCEPTION_ASSERTS: [
                                    Action(processing.exception.response_exception, {'expected': exp_exception}, ),
                                ],
                            }, },
                        consts.KEY_FINAL_ASSERTS: [
                            Action(publication.internal.does_not_exist, {})
                        ],
                    }
                    action_list = [action_def]
                else:
                    action_def = {
                        consts.KEY_ACTION: {
                            consts.KEY_CALL: Action(process_client.publish_workspace_publication,
                                                    {**tc_params[KEY_ACTION_PARAMS],
                                                     **rest_param_dict}),
                            consts.KEY_RESPONSE_ASSERTS: [
                                Action(processing.response.valid_post, {}),
                            ],
                        },
                        consts.KEY_FINAL_ASSERTS: [
                            Action(publication.rest.async_error_in_info_key, {'info_key': failed_info_key,
                                                                              'expected': exp_exception, }, ),
                        ],
                    }
                    if assert_no_bbox_and_crs:
                        action_def[consts.KEY_FINAL_ASSERTS].append(Action(publication.internal.no_bbox_and_crs, {}))
                    action_list = [action_def, VALIDATION_PATCH_ACTION]
                publ_name = f"{testcase}_post{test_case_postfix}"
                result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], publ_name)] = action_list

        for patch_key, patch_params in tc_params.get(KEY_PATCHES, {}).items():
            action_parametrization = util.get_test_case_parametrization(param_parametrization=REST_PARAMETRIZATION,
                                                                        only_first_parametrization=default_only_first_parametrization,
                                                                        default_params={**tc_params[KEY_ACTION_PARAMS],
                                                                                        **patch_params.get(KEY_ACTION_PARAMS, {})},
                                                                        action_parametrization=[('', None, []), ],
                                                                        )
            for test_case_postfix, _, _, rest_param_dict in action_parametrization:
                patch = [
                    {
                        consts.KEY_ACTION: {
                            consts.KEY_CALL: Action(process_client.publish_workspace_publication,
                                                    patch_params[KEY_PATCH_POST]),
                            consts.KEY_RESPONSE_ASSERTS: [
                                Action(processing.response.valid_post, {}),
                            ],
                        },
                        consts.KEY_FINAL_ASSERTS: [
                            *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                        ]
                    },
                ]
                rest_param_frozen_set = frozenset(rest_param_dict.items())
                default_exp_exception = copy.deepcopy(tc_params[KEY_EXPECTED_EXCEPTION][KEY_DEFAULT])
                exception_diff_post = tc_params[KEY_EXPECTED_EXCEPTION].get(rest_param_frozen_set, {})
                exception_diff_patch = patch_params.get(KEY_EXPECTED_EXCEPTION, {}).get(rest_param_frozen_set, {})
                exception_diff = asserts_util.recursive_dict_update(exception_diff_post, exception_diff_patch, keep_replace_key=True)
                exp_exception = asserts_util.recursive_dict_update(default_exp_exception, copy.deepcopy(exception_diff))
                is_sync = exp_exception.pop('sync')
                if is_sync:
                    action_def = {
                        consts.KEY_ACTION: {
                            consts.KEY_CALL: Action(process_client.patch_workspace_publication,
                                                    {**tc_params[KEY_ACTION_PARAMS],
                                                     **patch_params.get(KEY_ACTION_PARAMS, {}),
                                                     **rest_param_dict}),
                            consts.KEY_CALL_EXCEPTION: {
                                consts.KEY_EXCEPTION: LaymanError,
                                consts.KEY_EXCEPTION_ASSERTS: [
                                    Action(processing.exception.response_exception, {'expected': exp_exception}, ),
                                ],
                            }, },
                        consts.KEY_FINAL_ASSERTS: [
                            *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                        ]
                    }
                    patch.append(action_def)
                else:
                    action_def = {
                        consts.KEY_ACTION: {
                            consts.KEY_CALL: Action(process_client.patch_workspace_publication,
                                                    {**tc_params[KEY_ACTION_PARAMS],
                                                     **patch_params.get(KEY_ACTION_PARAMS, {}),
                                                     **rest_param_dict}),
                            consts.KEY_RESPONSE_ASSERTS: [
                                Action(processing.response.valid_post, {}),
                            ],
                        },
                        consts.KEY_FINAL_ASSERTS: [
                            Action(publication.rest.async_error_in_info_key, {'info_key': failed_info_key,
                                                                              'expected': exp_exception, }, ),
                        ],
                    }
                    if assert_no_bbox_and_crs:
                        action_def[consts.KEY_FINAL_ASSERTS].append(Action(publication.internal.no_bbox_and_crs, {}))

                    patch.append(action_def)
                    patch.append(VALIDATION_PATCH_ACTION)
                publ_name = f"{testcase}_patch_{patch_key}{test_case_postfix}"
                result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], publ_name)] = patch

    return result
