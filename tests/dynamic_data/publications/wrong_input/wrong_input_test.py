from copy import deepcopy
from contextlib import nullcontext as does_not_raise
from enum import Enum, unique
import os
import logging
import pytest

from layman import LaymanError, settings, app, util as layman_util
from layman.layer.util import EXTERNAL_TABLE_URI_PATTERN
from test_tools import process_client
from tests import EnumTestTypes, Publication
from tests.asserts import processing, util as asserts_util
from tests.asserts.final import publication as publication_asserts
from tests.asserts.final.publication import util as assert_utils
from tests.dynamic_data import base_test
from .. import common_publications as publications


@unique
class Key(Enum):
    REST_ARGS = 'rest_args'
    PUBLICATION_TYPE = 'publication_type'
    EXCEPTION = 'exception'
    EXPECTED_EXCEPTION = 'expected_exception'
    FAILED_INFO_KEY = 'failed_info_key'
    MANDATORY_CASES = 'mandatory_cases'
    RUN_ONLY_CASES = 'run_only_cases'
    SPECIFIC_CASES = 'specific_params'
    POST_BEFORE_PATCH_ARGS = 'post_before_patch_args'


WORKSPACE = 'dynamic_test_workspace_wrong_input'


@unique
class ParametrizationSets(Enum):
    ALL = frozenset([
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]),
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]),
    ])
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
    POST_NO_COMPRESS = frozenset([
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
    ])
    POST_PATCH_CHUNKS = frozenset([
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]),
    ])
    POST_PATCH_NO_CHUNKS = frozenset([
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]),
    ])
    POST_PATCH_NO_COMPRESS = frozenset([
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
        frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
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
        Key.RUN_ONLY_CASES: ParametrizationSets.ALL,
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
        Key.RUN_ONLY_CASES: ParametrizationSets.ALL,
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
        Key.RUN_ONLY_CASES: ParametrizationSets.POST_COMPRESS,
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
        Key.RUN_ONLY_CASES: ParametrizationSets.ALL,
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
        Key.RUN_ONLY_CASES: ParametrizationSets.PATCH_ALL,
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
        Key.RUN_ONLY_CASES: ParametrizationSets.POST_ALL,
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
        Key.RUN_ONLY_CASES: ParametrizationSets.ALL,
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
        Key.RUN_ONLY_CASES: ParametrizationSets.ALL,
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
        Key.RUN_ONLY_CASES: ParametrizationSets.ALL,
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
        Key.RUN_ONLY_CASES: ParametrizationSets.ALL,
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
        Key.RUN_ONLY_CASES: ParametrizationSets.ALL,
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
        Key.RUN_ONLY_CASES: ParametrizationSets.ALL,
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
        Key.RUN_ONLY_CASES: ParametrizationSets.POST_PATCH_NO_CHUNKS,
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
        Key.RUN_ONLY_CASES: {frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE])},
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
        Key.RUN_ONLY_CASES: {frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE])},
        Key.SPECIFIC_CASES: {},
    },
    'map_schema_3_0_0': {
        Key.PUBLICATION_TYPE: process_client.MAP_TYPE,
        Key.REST_ARGS: {
            'file_paths': [
                f'{DIRECTORY}/map_schema_3_0_0.json',
            ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 2,
            'data': {'expected': '2.x.x',
                     'parameter': 'file',
                     'reason': 'Invalid schema version'},
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: {frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE])},
        Key.SPECIFIC_CASES: {},
    },
    'map_unsupported_crs': {
        Key.PUBLICATION_TYPE: process_client.MAP_TYPE,
        Key.REST_ARGS: {
            'file_paths': [
                f'{DIRECTORY}/map_unsupported_crs.json',
            ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 4,
            'data': {'found': 'EPSG:3030',
                     'supported_values': settings.INPUT_SRS_LIST},
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: {frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE])},
        Key.SPECIFIC_CASES: {},
    },
    'layer_unsupported_overview_resampling': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': ['sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif'],
            'overview_resampling': 'no_overview_resampling',
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 2,
            'data': {'expected': 'Resampling method for gdaladdo utility, https://gdal.org/programs/gdaladdo.html',
                     'parameter': 'overview_resampling',
                     'detail': {'found': 'no_overview_resampling',
                                'supported_values': settings.OVERVIEW_RESAMPLING_METHOD_LIST}, },
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: ParametrizationSets.ALL,
        Key.SPECIFIC_CASES: {},
    },
    'layer_vector_overview_resampling': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': ['sample/layman.layer/small_layer.geojson'],
            'overview_resampling': 'nearest',
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 48,
            'message': 'Wrong combination of parameters',
            'data': 'Vector layers do not support overview resampling.',
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: ParametrizationSets.ALL,
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_CHUNKS: {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                },
            },
        },
    },
    'filename_not_match_time_regex': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'time_regex': r'non_existing_regex',
            'file_paths': [
                'tests/dynamic_data/publications/layer_timeseries/timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif'],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 48,
            'message': 'Wrong combination of parameters',
            'data': {
                'message': 'File does not match time_regex.',
                'expected': 'All main data files match time_regex parameter',
                'unmatched_filenames': ['S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif'],
            },
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: ParametrizationSets.ALL,
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_NO_CHUNKS_COMPRESS: {
                Key.EXPECTED_EXCEPTION: {
                    'data': {'unmatched_filenames': [
                        'temporary_zip_file.zip/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif'],
                    }
                },
            },
            ParametrizationSets.POST_PATCH_CHUNKS_COMPRESS: {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                    'data': {'unmatched_filenames': [
                        '{publication_name}.zip/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif'],
                    }
                },
            },
        },
    },
    'layer_overview_resampling_no_input_file': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': [],
            'overview_resampling': 'mode',
        },
        Key.POST_BEFORE_PATCH_ARGS: {
            'file_paths': ['sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif'],
            'overview_resampling': 'nearest',
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 48,
            'message': 'Wrong combination of parameters',
            'data': 'Parameter overview_resampling requires parameter file to be set.',
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: ParametrizationSets.PATCH_ALL,
        Key.SPECIFIC_CASES: {
            frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]): {
                Key.EXPECTED_EXCEPTION: {
                    'code': 2,
                    'message': 'Wrong parameter value',
                    'data': {
                        'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                        'files': ['temporary_zip_file.zip'],
                        'message': 'Zip file without data file inside.',
                        'parameter': 'file'
                    },
                },
            },
            frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]): {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                    'code': 2,
                    'message': 'Wrong parameter value',
                    'data': {
                        'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                        'files': ['{publication_name}.zip'],
                        'message': 'Zip file without data file inside.',
                        'parameter': 'file'
                    },
                },
            },
        },
    },
    'layer_name_211': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'name': 'a' * 211,
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 2,
            'data': {'parameter': 'layername',
                     'detail': 'Layer name too long (211), maximum allowed length is 210.',
                     },
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: ParametrizationSets.POST_ALL,
        Key.SPECIFIC_CASES: {},
    },
    'map_name_211': {
        Key.PUBLICATION_TYPE: process_client.MAP_TYPE,
        Key.REST_ARGS: {
            'name': 'a' * 211,
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 2,
            'data': {'parameter': 'mapname',
                     'detail': 'Map name too long (211), maximum allowed length is 210.',
                     },
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: {frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE])},
        Key.SPECIFIC_CASES: {},
    },
    'wrong_time_regex': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            **publications.SMALL_LAYER.definition,
            'time_regex': '[',
            'file_paths': [
                'tests/dynamic_data/publications/layer_timeseries/timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
            ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 2,
            'data': {'parameter': 'time_regex',
                     'expected': 'Regular expression',
                     },
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: ParametrizationSets.ALL,
        Key.SPECIFIC_CASES: {},
    },
    'vector_time_regex': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'time_regex': r'[0-9]{8}T[0-9]{6}Z(\?!.\*[0-9]{8}T[0-9]{6}Z.\*)',
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 48,
            'data': 'Vector layers are not allowed to be combined with `time_regex` parameter.',
        },
        Key.MANDATORY_CASES: {
            frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
        },
        Key.RUN_ONLY_CASES: ParametrizationSets.POST_ALL,
        Key.SPECIFIC_CASES: {
            frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]): {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                },
            }
        },
    },
    'raster_vector_time_regex': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'time_regex': r'[0-9]{8}T[0-9]{6}Z(\?!.\*[0-9]{8}T[0-9]{6}Z.\*)',
            'file_paths': ['sample/layman.layer/sample_jp2_rgb.jp2',
                           'sample/layman.layer/single_point.dbf',
                           'sample/layman.layer/single_point.prj',
                           'sample/layman.layer/single_point.shp',
                           'sample/layman.layer/single_point.shx',
                           'sample/layman.layer/single_point.qpj',
                           ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 2,
            'data': {'expected': 'All main files with the same extension.',
                     'files': ['sample_jp2_rgb.jp2', 'single_point.shp'],
                     'extensions': ['.jp2', '.shp'],
                     'parameter': 'file',
                     },
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: ParametrizationSets.POST_ALL,
        Key.SPECIFIC_CASES: {
            frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]): {
                Key.EXPECTED_EXCEPTION: {
                    'data': {'files': ['temporary_zip_file.zip/sample_jp2_rgb.jp2', 'temporary_zip_file.zip/single_point.shp'], },
                },
            },
            frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]): {
                Key.EXPECTED_EXCEPTION: {
                    'data': {'files': ['{publication_name}.zip/sample_jp2_rgb.jp2', '{publication_name}.zip/single_point.shp'], },
                    'sync': False,
                },
            },
        },
    },
    'dif_raster_types_time_regex': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'time_regex': r'[0-9]{8}T[0-9]{6}Z(\?!.\*[0-9]{8}T[0-9]{6}Z.\*)',
            'file_paths': ['sample/layman.layer/sample_jp2_j2w_rgb.j2w',
                           'sample/layman.layer/sample_jp2_j2w_rgb.jp2',
                           'sample/layman.layer/sample_jpeg_jgw_rgb.jgw',
                           'sample/layman.layer/sample_jpeg_jgw_rgb.jpeg',
                           ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 2,
            'data': {'expected': 'All main files with the same extension.',
                     'files': ['sample_jp2_j2w_rgb.jp2', 'sample_jpeg_jgw_rgb.jpeg', ],
                     'extensions': ['.jp2', '.jpeg'],
                     'parameter': 'file',
                     },
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: ParametrizationSets.POST_ALL,
        Key.SPECIFIC_CASES: {
            frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]): {
                Key.EXPECTED_EXCEPTION: {
                    'data': {'files': ['temporary_zip_file.zip/sample_jp2_j2w_rgb.jp2', 'temporary_zip_file.zip/sample_jpeg_jgw_rgb.jpeg', ], },
                },
            },
            frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]): {
                Key.EXPECTED_EXCEPTION: {
                    'data': {'files': ['{publication_name}.zip/sample_jp2_j2w_rgb.jp2',
                                       '{publication_name}.zip/sample_jpeg_jgw_rgb.jpeg', ], },
                    'sync': False,
                },
            },
        },
    },
    'raster_and_zip_raster_time_regex': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'time_regex': r'[0-9]{8}T[0-9]{6}Z(\?!.\*[0-9]{8}T[0-9]{6}Z.\*)',
            'file_paths': ['sample/layman.layer/sample_jp2_rgb.jp2',
                           'sample/layman.layer/sample_jp2_rgb.zip',
                           ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 2,
            'data': {'expected': 'One compressed file or one or more uncompressed files.',
                     'files': ['sample_jp2_rgb.jp2', 'sample_jp2_rgb.zip', ],
                     'parameter': 'file',
                     },
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: ParametrizationSets.POST_NO_COMPRESS,
        Key.SPECIFIC_CASES: {},
    },
    'different_rasters_time_regex': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'time_regex': r'cz_[0-9]{4}',
            'file_paths': ['tests/dynamic_data/publications/crs/rasters/cz_4326.tif',
                           'tests/dynamic_data/publications/crs/rasters/cz_32633.tif',
                           ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 2,
            'data': {'expected': 'All main files with the same CRS.',
                     'crs': ['EPSG:32633', 'EPSG:4326', ],
                     'parameter': 'file',
                     },
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: ParametrizationSets.POST_ALL,
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_CHUNKS: {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                },
            },
        },
    },
    'different_bands_rasters_time_regex': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'time_regex': r'[a-z]{5}',
            'file_paths': ['sample/layman.layer/sample_tif_rgba.tif',
                           'sample/layman.layer/sample_tif_rgb_nodata.tif',
                           ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 2,
            'data': {'expected': 'All main files with the same color interpretations.',
                     'color_interpretations': [['Red', 'Green', 'Blue'], ['Red', 'Green', 'Blue', 'Alpha']],
                     'parameter': 'file',
                     },
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: ParametrizationSets.POST_ALL,
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_CHUNKS: {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                },
            },
        },
    },
    'non_data_file_without_data_file': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': ['sample/layman.layer/sample_jp2_j2w_rgb.j2w'],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 2,
            'message': 'Wrong parameter value',
            'data': {
                'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                'files': ['sample_jp2_j2w_rgb.j2w'],
                'message': 'No data file in input.',
                'parameter': 'file',
            },
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: ParametrizationSets.ALL,
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_NO_CHUNKS_COMPRESS: {
                Key.EXPECTED_EXCEPTION: {
                    'data': {'files': ['temporary_zip_file.zip/sample_jp2_j2w_rgb.j2w'],
                             'message': 'Zip file without data file inside.', }
                },
            },
            ParametrizationSets.POST_PATCH_CHUNKS_COMPRESS: {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                    'data': {'files': ['{publication_name}.zip/sample_jp2_j2w_rgb.j2w'],
                             'message': 'Zip file without data file inside.', }
                },
            },
        },
    },
    'patch_with_time_regex_without_data_file': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'time_regex': r'[0-9]{8}T[0-9]{6}Z(\?!.\*[0-9]{8}T[0-9]{6}Z.\*)',
        },
        Key.POST_BEFORE_PATCH_ARGS: {
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                'tests/dynamic_data/publications/layer_timeseries/timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                'tests/dynamic_data/publications/layer_timeseries/timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.TIF',
            ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 48,
            'message': 'Wrong combination of parameters',
            'data': 'Parameter time_regex is allowed only in combination with files.',
        },
        Key.MANDATORY_CASES: {frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE])},
        Key.RUN_ONLY_CASES: {frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE])},
        Key.SPECIFIC_CASES: {},
    },
    'time_regex_with_non_data_file': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': ['sample/layman.layer/sample_jp2_j2w_rgb.j2w'],
            'time_regex': r'[0-9]{8}T[0-9]{6}Z(\?!.\*[0-9]{8}T[0-9]{6}Z.\*)',
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 2,
            'message': 'Wrong parameter value',
            'data': {
                'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                'files': ['sample_jp2_j2w_rgb.j2w'],
                'message': 'No data file in input.',
                'parameter': 'file',
            },
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: ParametrizationSets.ALL,
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_NO_CHUNKS_COMPRESS: {
                Key.EXPECTED_EXCEPTION: {
                    'data': {'files': ['temporary_zip_file.zip/sample_jp2_j2w_rgb.j2w'],
                             'message': 'Zip file without data file inside.', }
                },
            },
            ParametrizationSets.POST_PATCH_CHUNKS_COMPRESS: {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                    'data': {'files': ['{publication_name}.zip/sample_jp2_j2w_rgb.j2w'],
                             'message': 'Zip file without data file inside.', }
                },
            },
        },
    },
    'too_long_filename_with_time_regexp': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                f'{DIRECTORY}/211_too_long_name_20220319_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.zip',
            ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 48,
            'message': 'Wrong combination of parameters',
            'data': {
                'message': 'Too long filename in timeseries.',
                'expected': 'All files names shorter than 211 characters',
                'too_long_filenames': [
                    '211_too_long_name_20220319_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.zip/211_too_long_name_20220319_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.tif'],
            },
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: ParametrizationSets.POST_PATCH_NO_COMPRESS,
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_CHUNKS: {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                    'data': {'too_long_filenames': [
                        '{publication_name}.zip/211_too_long_name_20220319_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.tif']}
                },
            },
        },
    },
    'unsafe_timeseries_filename_with_dot': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                f'{DIRECTORY}/.20220316.tif',
            ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 48,
            'message': 'Wrong combination of parameters',
            'data': {
                'message': 'Unsafe filename in timeseries.',
                'expected': 'All slugified file names matching pattern ^(?![.])[a-zA-Z0-9_.-]+$',
                'unsafe_slugified_filenames': ['.20220316.tif'],
            },
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: ParametrizationSets.ALL,
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_CHUNKS_COMPRESS: {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                },
            },
        },
    },
    'unsafe_timeseries_filename_with_cyrillic': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                f'{DIRECTORY}/річка_20220316.tif',
            ],
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 48,
            'message': 'Wrong combination of parameters',
            'data': {
                'message': 'Unsafe filename in timeseries.',
                'expected': 'All slugified file names matching pattern ^(?![.])[a-zA-Z0-9_.-]+$',
                'unsafe_slugified_filenames': ['річка_20220316.tif'],
            },
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: ParametrizationSets.ALL,
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_CHUNKS_COMPRESS: {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                },
            },
        },
    },
    'raster_wrong_crs': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': [
                'tests/dynamic_data/publications/layer_timeseries/timeseries_tif/S2A_MSIL2A_20220316T100031.0.tif'
            ],
            'crs': 'EPSG:4326'
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'wms',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 500,
            'sync': False,
            'code': 53,
            'message': 'Error when publishing on GeoServer. It happens for example for raster files with wrong explicit CRS.',
        },
        Key.MANDATORY_CASES: {
            frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
        },
        Key.RUN_ONLY_CASES: ParametrizationSets.POST_ALL,
        Key.SPECIFIC_CASES: {},
    },
    'duplicate_filename_differs_in_case': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': [
                f'{DIRECTORY}/small_layer.geojson',
                f'{DIRECTORY}/small_layer.README.txt',
                f'{DIRECTORY}/small_layer.readme.txt',
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
                'parameter': 'file',
                'message': 'Two or more input file names map to the same name.',
                'expected': 'Input file names that differ at least in one letter (ignoring case and diacritics) or number.',
                'similar_filenames_mapping': {
                    'small_layer.README.txt': '{publication_name}.readme.txt',
                    'small_layer.readme.txt': '{publication_name}.readme.txt',
                },
            },
        },
        Key.MANDATORY_CASES: ParametrizationSets.SIMPLE_POST_PATCH,
        Key.RUN_ONLY_CASES: ParametrizationSets.POST_PATCH_NO_COMPRESS,
        Key.SPECIFIC_CASES: {},
    },
    'duplicate_filename_differs_in_diacritics': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'time_regex': r'[0-9]{8}',
            'file_paths': [
                f'{DIRECTORY}/snimek_20220316.tif',
                f'{DIRECTORY}/snímek_20220316.tif',
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
                'parameter': 'file',
                'message': 'Two or more input file names map to the same name.',
                'expected': 'Input file names that differ at least in one letter (ignoring case and diacritics) or number.',
                'similar_filenames_mapping': {
                    'snimek_20220316.tif': 'snimek_20220316.tif',
                    'snímek_20220316.tif': 'snimek_20220316.tif',
                },
            },
        },
        Key.MANDATORY_CASES: ParametrizationSets.SIMPLE_POST_PATCH,
        Key.RUN_ONLY_CASES: ParametrizationSets.ALL,
        Key.SPECIFIC_CASES: {
            ParametrizationSets.POST_PATCH_NO_CHUNKS_COMPRESS: {
                Key.EXPECTED_EXCEPTION: {
                    'data': {
                        'similar_filenames_mapping': {
                            asserts_util.KEY_REPLACE: True,
                            'temporary_zip_file.zip/snimek_20220316.tif': 'snimek_20220316.tif',
                            'temporary_zip_file.zip/snímek_20220316.tif': 'snimek_20220316.tif',
                        },
                    },
                },
            },
            ParametrizationSets.POST_PATCH_CHUNKS_COMPRESS: {
                Key.EXPECTED_EXCEPTION: {
                    'sync': False,
                    'data': {
                        'similar_filenames_mapping': {
                            asserts_util.KEY_REPLACE: True,
                            '{publication_name}.zip/snimek_20220316.tif': 'snimek_20220316.tif',
                            '{publication_name}.zip/snímek_20220316.tif': 'snimek_20220316.tif',
                        },
                    },
                },
            },
        },
    },
    'none_file_none_external_table_uri': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': [],
            'external_table_uri': '',
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
            'sync': True,
            'code': 1,
            'message': 'Missing parameter',
            'data': {
                'parameters': ['file', 'external_table_uri'],
                'message': 'Both `file` and `external_table_uri` parameters are empty',
                'expected': 'One of the parameters is filled.',
            },
        },
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: {frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE])},
        Key.SPECIFIC_CASES: {},
    },
    'file_and_external_table_uri': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'file_paths': ['sample/layman.layer/small_layer.geojson'],
            'external_table_uri': 'postgresql://username:password@host:port/dbname?table=table_name&geo_column=geo_column_name',
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
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
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: ParametrizationSets.POST_PATCH_NO_COMPRESS,
        Key.SPECIFIC_CASES: {},
    },
    'partial_external_table_uri': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'external_table_uri': 'external_table_uri',
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
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
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: ParametrizationSets.SIMPLE_POST_PATCH,
        Key.SPECIFIC_CASES: {},
    },
    'crs_and_external_table_uri_post': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'crs': 'EPSG:4326',
            'external_table_uri': 'postgresql://username:password@host:port/dbname?table=table_name&geo_column=geo_column_name',
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
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
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: {frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE])},
        Key.SPECIFIC_CASES: {},
    },
    'crs_and_external_table_uri_patch': {
        Key.PUBLICATION_TYPE: process_client.LAYER_TYPE,
        Key.REST_ARGS: {
            'crs': 'EPSG:4326',
            'external_table_uri': 'postgresql://username:password@host:port/dbname?table=table_name&geo_column=geo_column_name',
            'skip_asserts': True,
        },
        Key.EXCEPTION: LaymanError,
        Key.FAILED_INFO_KEY: 'file',
        Key.EXPECTED_EXCEPTION: {
            'http_code': 400,
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
        Key.MANDATORY_CASES: {},
        Key.RUN_ONLY_CASES: {frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE])},
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

        run_only_cases = all_params.pop(Key.RUN_ONLY_CASES)
        run_only_cases = run_only_cases.value if isinstance(run_only_cases,
                                                            ParametrizationSets) else run_only_cases
        ignore_cases = ParametrizationSets.ALL.value.difference(run_only_cases)
        for case in ignore_cases:
            assert case not in specific_types, f'key={key},\ncase={case},\nspecific_types={specific_types}'
            specific_types[case] = EnumTestTypes.IGNORE

        specific_params_def = all_params.pop(Key.SPECIFIC_CASES)
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

        publication_name = rest_args.pop('name', None)
        publication = Publication(workspace=WORKSPACE,
                                  type=publ_type,
                                  name=publication_name,
                                  ) if publication_name else None

        test_case = base_test.TestCaseType(key=key,
                                           publication=publication,
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
    if 'data' in exception_info and isinstance(exception_info['data'], dict):
        if 'path' in exception_info['data']:
            exception_info['data']['path'] = exception_info['data']['path'].format(**format_variables)
        if 'file' in exception_info['data']:
            exception_info['data']['file'] = exception_info['data']['file'].format(**format_variables)
        if 'files' in exception_info['data']:
            exception_info['data']['files'] = [file.format(**format_variables) for file in exception_info['data']['files']]
        if 'unmatched_filenames' in exception_info['data']:
            exception_info['data']['unmatched_filenames'] = [file.format(**format_variables) for file in exception_info['data']['unmatched_filenames']]
        if 'too_long_filenames' in exception_info['data']:
            exception_info['data']['too_long_filenames'] = [file.format(**format_variables) for file in exception_info['data']['too_long_filenames']]
        if 'similar_filenames_mapping' in exception_info['data']:
            exception_info['data']['similar_filenames_mapping'] = {key.format(**format_variables): value.format(**format_variables) for
                                                                   key, value in exception_info['data']['similar_filenames_mapping'].items()}


@pytest.mark.usefixtures('ensure_external_db')
class TestPublication(base_test.TestSingleRestPublication):
    workspace = WORKSPACE
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
            if publication.type == process_client.LAYER_TYPE:
                with app.app_context():
                    publ_info = layman_util.get_publication_info(publication.workspace, publication.type, publication.name,
                                                                 context={'keys': ['wfs_wms_status']})

                assert publ_info['_wfs_wms_status'] == settings.EnumWfsWmsStatus.NOT_AVAILABLE

                publication_asserts.internal_rest.same_title_and_wfs_wms_status_in_source_and_rest_multi(workspace=publication.workspace,
                                                                                                         publ_type=publication.type,
                                                                                                         name=publication.name,
                                                                                                         headers=None,
                                                                                                         )
