from copy import deepcopy
from contextlib import nullcontext as does_not_raise
from enum import Enum, unique
import os
import logging
import pytest

from layman import LaymanError, settings
from test_tools import process_client
from tests import EnumTestTypes, Publication
from tests.asserts import processing
from tests.asserts.final import publication as publication_asserts
from tests.asserts.final.publication import util as assert_utils
from tests.dynamic_data import base_test


@unique
class Key(Enum):
    REST_ARGS = 'rest_args'
    PUBLICATION_TYPE = 'publication_type'
    EXCEPTION = 'exception'
    EXPECTED_EXCEPTION = 'expected_exception'
    FAILED_INFO_KEY = 'failed_info_key'
    MANDATORY_CASES = 'mandatory_cases'
    IGNORED_CASES = 'ignored_cases'
    SPECIFIC_CASES = 'specific_params'
    POST_BEFORE_PATCH_ARGS = 'post_before_patch_args'


@unique
class ParametrizationSets(Enum):
    SIMPLE_POST_PATCH = frozenset([
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
    ])
    POST_PATCH_NO_CHUNKS_COMPRESS = frozenset([
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]),
    ])
    POST_PATCH_CHUNKS_COMPRESS = frozenset([
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]),
    ])
    NOT_POST_COMPRESS = frozenset([
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]),
    ])
    POST_ALL = frozenset([
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]),
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]),
    ])
    PATCH_ALL = frozenset([
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]),
    ])
    POST_COMPRESS = frozenset([
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]),
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]),
    ])
    POST_PATCH_CHUNKS = frozenset([
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]),
    ])
    NOT_SIMPLE_POST = frozenset([
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]),
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]),
    ])


DIRECTORY = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)

pytest_generate_tests = base_test.pytest_generate_tests


TESTCASES = {
    'shp_without_dbf': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': [
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.cpg',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.README.html',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shx',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.VERSION.txt',
            ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 18,
            'message': 'Missing one or more ShapeFile files.',
            'data': {'missing_extensions': ['.dbf', '.prj'],
                     'suggestion': 'Missing .prj file can be fixed also by setting "crs" parameter.',
                     'path': 'ne_110m_admin_0_boundary_lines_land.shp',
                     },
        },
        Key.MANDATORY_CASES: ParametrizationSets.SIMPLE_POST_PATCH,
        Key.IGNORED_CASES: {},
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_NO_CHUNKS_COMPRESS: {
                Key.EXPECTED_EXCEPTION: {
                    'data': {'path': 'temporary_zip_file.zip/ne_110m_admin_0_boundary_lines_land.shp'},
                },
            },
            ParametrizationSets.POST_PATCH_CHUNKS_COMPRESS: {
                Key.EXPECTED_EXCEPTION: {
                    'data': {'path': '{publication_name}.zip/ne_110m_admin_0_boundary_lines_land.shp'},
                    'sync': False,
                },
            },
        },
    },
    'shp_without_prj': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': [
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.cpg',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.dbf',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shx',
            ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 18,
            'message': 'Missing one or more ShapeFile files.',
            'data': {'missing_extensions': ['.prj'],
                     'suggestion': 'Missing .prj file can be fixed also by setting "crs" parameter.',
                     'path': 'ne_110m_admin_0_boundary_lines_land.shp',
                     },
        },
        Key.MANDATORY_CASES: {},
        Key.IGNORED_CASES: {},
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_NO_CHUNKS_COMPRESS: {
                Key.EXPECTED_EXCEPTION: {
                    'data': {'path': 'temporary_zip_file.zip/ne_110m_admin_0_boundary_lines_land.shp'},
                },
            },
            ParametrizationSets.POST_PATCH_CHUNKS_COMPRESS: {
                Key.EXPECTED_EXCEPTION: {
                    'data': {'path': '{publication_name}.zip/ne_110m_admin_0_boundary_lines_land.shp'},
                    'sync': False,
                },
            },
        },
    },
    'empty_zip': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': [],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 2,
            'data': {'parameter': 'file',
                     'message': 'Zip file without data file inside.',
                     'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                     'files': [
                         'temporary_zip_file.zip',
                     ],
                     },
        },
        Key.MANDATORY_CASES: {
            frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE])
        },
        Key.IGNORED_CASES: ParametrizationSets.NOT_POST_COMPRESS,
        Key.SPECIFIC_CASES: {
            frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]): {
                Key.EXPECTED_EXCEPTION: {
                    'data': {'files': ['{publication_name}.zip']},
                    'sync': False,
                },
            },
        },
    },
    'tif_with_qml': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': ['sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif'],
            'style_file': 'sample/style/ne_10m_admin_0_countries.qml',
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 48,
            'message': 'Wrong combination of parameters',
            'data': 'Raster layers are not allowed to have QML style.',
        },
        Key.MANDATORY_CASES: ParametrizationSets.SIMPLE_POST_PATCH,
        Key.IGNORED_CASES: {},
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_CHUNKS_COMPRESS: {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                },
            },
        },
    },
    'tif_with_qml_data_without_style': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': ['sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif'],
        },
        Key.POST_BEFORE_PATCH_ARGS: {
            'file_paths': ['sample/layman.layer/sample_point_cz.geojson'],
            'style_file': 'sample/layman.layer/sample_point_cz.qml',
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 48,
            'message': 'Wrong combination of parameters',
            'data': 'Raster layers are not allowed to have QML style.',
        },
        Key.MANDATORY_CASES: {frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE])},
        Key.IGNORED_CASES: ParametrizationSets.POST_ALL,
        Key.SPECIFIC_CASES: {
            frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]): {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                },
            },
        },
    },
    'non_readable_raster': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': [f'{DIRECTORY}/non_readable_raster.tif'],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 2,
            'message': 'Wrong parameter value',
            'data': {'parameter': 'file',
                     'message': 'Unable to open raster file.',
                     'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                     'file': '/layman_data_test/workspaces/{workspace}/layers/{publication_name}/input_file/{publication_name}.tif',
                     },
        },
        Key.MANDATORY_CASES: {frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE])},
        Key.IGNORED_CASES: ParametrizationSets.PATCH_ALL,
        Key.SPECIFIC_CASES: {
            frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]): {
                Key.EXPECTED_EXCEPTION: {
                    'data': {
                        'file': '/vsizip//layman_data_test/workspaces/{workspace}/layers/{publication_name}/input_file/{publication_name}.zip/non_readable_raster.tif',
                    }
                },
            },
            frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]): {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                    'data': {
                        'file': '/layman_data_test/workspaces/{workspace}/layers/{publication_name}/input_file/{publication_name}.tif'
                    }
                },
            },
            frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]): {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                    'data': {
                        'file': '/vsizip//layman_data_test/workspaces/{workspace}/layers/{publication_name}/input_file/{publication_name}.zip/non_readable_raster.tif',
                    }
                },
            },
        },
    },
    'pgw_png_unsupported_crs': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': ['sample/layman.layer/sample_png_pgw_rgba.pgw',
                           'sample/layman.layer/sample_png_pgw_rgba.png', ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 4,
            'message': 'Unsupported CRS of data file',
            'data': {'found': None, 'supported_values': settings.INPUT_SRS_LIST},
        },
        Key.MANDATORY_CASES: ParametrizationSets.SIMPLE_POST_PATCH,
        Key.IGNORED_CASES: {},
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_CHUNKS: {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                },
            },
        },
    },
    'png_without_pgw': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': ['sample/layman.layer/sample_png_pgw_rgba.png', ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 4,
            'message': 'Unsupported CRS of data file',
            'data': {'found': None, 'supported_values': settings.INPUT_SRS_LIST},
        },
        Key.MANDATORY_CASES: {},
        Key.IGNORED_CASES: {},
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_CHUNKS: {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                },
            },
        },
    },
    'shp_with_unsupported_epsg': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': [
                f'{DIRECTORY}/sample_point_cz_2154.cpg',
                f'{DIRECTORY}/sample_point_cz_2154.dbf',
                f'{DIRECTORY}/sample_point_cz_2154.prj',
                f'{DIRECTORY}/sample_point_cz_2154.qmd',
                f'{DIRECTORY}/sample_point_cz_2154.shp',
                f'{DIRECTORY}/sample_point_cz_2154.shx',
            ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 4,
            'message': 'Unsupported CRS of data file',
            'data': {'found': 'EPSG:2154', 'supported_values': settings.INPUT_SRS_LIST},
        },
        Key.MANDATORY_CASES: {},
        Key.IGNORED_CASES: {},
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_CHUNKS: {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                },
            },
        },
    },
    'tif_with_unsupported_epsg': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': [f'{DIRECTORY}/sample_tif_rgb_2154.tif', ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 4,
            'message': 'Unsupported CRS of data file',
            'data': {'found': 'EPSG:2154', 'supported_values': settings.INPUT_SRS_LIST},
        },
        Key.MANDATORY_CASES: {},
        Key.IGNORED_CASES: {},
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_CHUNKS: {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                },
            },
        },
    },
    'two_main_files': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': [
                'sample/layman.layer/small_layer.geojson',
                'sample/layman.layer/sample_tif_rgb.tif',
            ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 2,
            'message': 'Wrong parameter value',
            'data': {
                'expected': 'At most one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or timeseries with time_regex parameter.',
                'files': [
                    'sample_tif_rgb.tif',
                    'small_layer.geojson'],
                'parameter': 'file'},
        },
        Key.MANDATORY_CASES: ParametrizationSets.SIMPLE_POST_PATCH,
        Key.IGNORED_CASES: {},
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_NO_CHUNKS_COMPRESS: {
                Key.EXPECTED_EXCEPTION: {
                    'data': {
                        'files': [
                            'temporary_zip_file.zip/sample_tif_rgb.tif',
                            'temporary_zip_file.zip/small_layer.geojson'],
                    }
                },
            },
            ParametrizationSets.POST_PATCH_CHUNKS_COMPRESS: {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                    'data': {
                        'files': [
                            '{publication_name}.zip/sample_tif_rgb.tif',
                            '{publication_name}.zip/small_layer.geojson'],
                    }
                },
            },
        },
    },
    'two_zip_files': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': [
                'tmp/sm5/vektor/sm5.zip',
                f'{DIRECTORY}/layer_with_two_main_files.zip',
            ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 2,
            'data': {'parameter': 'file',
                     'expected': 'At most one file with extensions: .zip',
                     'files': [
                         'sm5.zip',
                         'layer_with_two_main_files.zip',
                     ],
                     },
        },
        Key.MANDATORY_CASES: {},
        Key.IGNORED_CASES: {},
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_NO_CHUNKS_COMPRESS: {
                Key.EXPECTED_EXCEPTION: {
                    'data': {
                        'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                        'files': [
                            'temporary_zip_file.zip/sm5.zip',
                            'temporary_zip_file.zip/layer_with_two_main_files.zip',
                        ],
                        'message': 'Zip file without data file inside.',
                        'parameter': 'file'
                    },
                },
            },
            ParametrizationSets.POST_PATCH_CHUNKS_COMPRESS: {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                    'data': {
                        'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                        'files': [
                            '{publication_name}.zip/sm5.zip',
                            '{publication_name}.zip/layer_with_two_main_files.zip',
                        ],
                        'message': 'Zip file without data file inside.',
                        'parameter': 'file'
                    },
                },
            },
        },
    },
    'tif_with_unsupported_bands': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': ['sample/layman.layer/sample_tif_rg.tif', ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 2,
            'message': 'Wrong parameter value',
            'data': {'parameter': 'file',
                     'expected': 'Any of color interpretations [Gray], '
                                 '[Gray, Alpha], [Palette], [Red, Green, Blue], '
                                 '[Red, Green, Blue, Alpha].',
                     'found': ['Red', 'Green']
                     },
        },
        Key.MANDATORY_CASES: ParametrizationSets.SIMPLE_POST_PATCH,
        Key.IGNORED_CASES: ParametrizationSets.POST_PATCH_CHUNKS,
        Key.SPECIFIC_CASES: {},
    },
    'epsg_4326_en': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': [
                f'{DIRECTORY}/small_layer_4326_en.shp',
                f'{DIRECTORY}/small_layer_4326_en.dbf',
                f'{DIRECTORY}/small_layer_4326_en.prj',
                f'{DIRECTORY}/small_layer_4326_en.shx',
            ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 4,
            'data': {'found': None, 'supported_values': settings.INPUT_SRS_LIST},
        },
        Key.MANDATORY_CASES: {},
        Key.IGNORED_CASES: ParametrizationSets.NOT_SIMPLE_POST,
        Key.SPECIFIC_CASES: {},
    },
    'map_schema_1_0_0': {
        Key.PUBLICATION_TYPE: process_client.MAP_TYPE,
        Key.REST_ARGS: {
            'file_paths': [
                f'{DIRECTORY}/map_schema_1_1_0.json',
            ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 2,
            'data': {'expected': 'JSON file according schema `https://github.com/hslayers/map-compositions`, version 2',
                     'parameter': 'file',
                     'reason': 'Missing key `describedBy`'},
        },
        Key.MANDATORY_CASES: {},
        Key.IGNORED_CASES: ParametrizationSets.NOT_SIMPLE_POST,
        Key.SPECIFIC_CASES: {},
    },
}


def generate_test_cases():
    tc_list = []
    for key, test_case_params in TESTCASES.items():
        all_params = deepcopy(test_case_params)
        rest_args = all_params.pop(Key.REST_ARGS)

        mandatory_cases = all_params.pop(Key.MANDATORY_CASES)
        mandatory_cases = mandatory_cases.value if isinstance(mandatory_cases,
                                                              ParametrizationSets) else mandatory_cases
        specific_types = {tc: EnumTestTypes.MANDATORY for tc in mandatory_cases}

        ignore_cases = all_params.pop(Key.IGNORED_CASES)
        ignore_cases = ignore_cases.value if isinstance(ignore_cases,
                                                        ParametrizationSets) else ignore_cases
        for case in ignore_cases:
            assert case not in specific_types, f'key={key},\ncase={case},\nspecific_types={specific_types}'
            specific_types[case] = EnumTestTypes.IGNORE

        specific_params_def = all_params.pop(Key.SPECIFIC_CASES)
        specific_params_def = specific_params_def.value if isinstance(specific_params_def,
                                                                      ParametrizationSets) else specific_params_def
        specific_params = {}
        for parametrization_key, parametrization_value in specific_params_def.items():
            parametrization_key = parametrization_key.value if isinstance(parametrization_key,
                                                                          ParametrizationSets) else parametrization_key
            if all(isinstance(parametrization_item, frozenset) for parametrization_item in parametrization_key):
                for parametrization_item in parametrization_key:
                    specific_params[parametrization_item] = parametrization_value
            else:
                specific_params[parametrization_key] = parametrization_value

        post_before_patch_args = test_case_params.pop(Key.POST_BEFORE_PATCH_ARGS, {})
        publ_type = all_params.pop(Key.PUBLICATION_TYPE)
        test_case = base_test.TestCaseType(key=key,
                                           publication_type=publ_type,
                                           type=EnumTestTypes.OPTIONAL,
                                           specific_types=specific_types,
                                           rest_args=rest_args,
                                           params=all_params,
                                           specific_params=specific_params,
                                           post_before_patch_args=post_before_patch_args,
                                           marks=[pytest.mark.xfail(reason="Not yet implemented.")]
                                           if test_case_params.get('xfail') else []
                                           )
        tc_list.append(test_case)
    return tc_list


def format_exception(exception_info: dict, format_variables: dict):
    if 'path' in exception_info['data']:
        exception_info['data']['path'] = exception_info['data']['path'].format(**format_variables)
    if 'file' in exception_info['data']:
        exception_info['data']['file'] = exception_info['data']['file'].format(**format_variables)
    if 'files' in exception_info['data']:
        exception_info['data']['files'] = [file.format(**format_variables) for file in exception_info['data']['files']]


@pytest.mark.usefixtures('ensure_external_db')
class TestPublication(base_test.TestSingleRestPublication):
    workspace = 'dynamic_test_workspace_wrong_input'
    test_cases = generate_test_cases()
    publication_type = None
    rest_parametrization = [
        base_test.RestMethod,
        base_test.WithChunksDomain,
        base_test.CompressDomain,
    ]

    def test_publication(self, publication: Publication, rest_method, rest_args, params):
        """Parametrized using pytest_generate_tests"""

        exp_exception = params[Key.EXPECTED_EXCEPTION]
        is_sync = exp_exception.pop('sync')
        format_exception(exp_exception, {
            'publication_name': publication.name,
            'workspace': publication.workspace,
        })
        exception = pytest.raises(params[Key.EXCEPTION]) if is_sync else does_not_raise()
        with exception as exception_info:
            response = rest_method(publication, args=rest_args)
        if is_sync:
            processing.exception.response_exception(expected=exp_exception, thrown=exception_info)
            if rest_method == self.patch_publication:  # pylint: disable=W0143
                assert_utils.is_publication_valid_and_complete(publication)
        else:
            processing.response.valid_post(workspace=publication.workspace,
                                           publ_type=publication.type,
                                           name=publication.name,
                                           response=response,
                                           )
            rest_publication_detail = process_client.get_workspace_publication(publication_type=publication.type,
                                                                               workspace=publication.workspace,
                                                                               name=publication.name,
                                                                               )
            failed_info_key = params[Key.FAILED_INFO_KEY]
            publication_asserts.rest.async_error_in_info_key(rest_publication_detail=rest_publication_detail,
                                                             info_key=failed_info_key,
                                                             expected=exp_exception,
                                                             )
