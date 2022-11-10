import copy
import os
import logging

from layman import LaymanError, settings
from tests.asserts import util as asserts_util
import tests.asserts.processing as processing
import tests.asserts.final.publication as publication
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
    'with_chunks': {False: 'sync', True: 'chunks'},
    'compress': {False: '', True: 'zipped'},
}

TESTCASES = {
    'shp_without_dbf': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.cpg',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.README.html',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shx',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.VERSION.txt',
            ],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 18,
                          'message': 'Missing one or more ShapeFile files.',
                          'detail': {'missing_extensions': ['.dbf', '.prj'],
                                     'suggestion': 'Missing .prj file can be fixed also by setting "crs" parameter.',
                                     'path': 'ne_110m_admin_0_boundary_lines_land.shp',
                                     },
                          },
            frozenset([('compress', True), ('with_chunks', False)]): {
                'detail': {'path': 'temporary_zip_file.zip/ne_110m_admin_0_boundary_lines_land.shp'}},
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
                'detail': {'path': 'shp_without_dbf_post_chunks_zipped.zip/ne_110m_admin_0_boundary_lines_land.shp'}},
        },
        KEY_PATCHES: {
            'all_files': {
                KEY_PATCH_POST: dict(),
                KEY_EXPECTED_EXCEPTION: {
                    frozenset([('compress', True), ('with_chunks', False)]): {
                        'detail': {'path': 'temporary_zip_file.zip/ne_110m_admin_0_boundary_lines_land.shp'}},
                    frozenset([('compress', True), ('with_chunks', True)]): {
                        'detail': {'path': 'shp_without_dbf_patch_all_files_chunks_zipped.zip/ne_110m_admin_0_boundary_lines_land.shp'}}
                },
            },
        },
    },
    'shp_without_prj': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.cpg',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.dbf',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shx',
            ],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 18,
                          'message': 'Missing one or more ShapeFile files.',
                          'detail': {'missing_extensions': ['.prj'],
                                     'suggestion': 'Missing .prj file can be fixed also by setting "crs" parameter.',
                                     'path': 'ne_110m_admin_0_boundary_lines_land.shp',
                                     },
                          },
            frozenset([('compress', True), ('with_chunks', False)]): {
                'detail': {'path': 'temporary_zip_file.zip/ne_110m_admin_0_boundary_lines_land.shp'}},
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
                'detail': {'path': 'shp_without_prj_post_chunks_zipped.zip/ne_110m_admin_0_boundary_lines_land.shp'}},
        },
        KEY_PATCHES: {
            'all_files': {
                KEY_PATCH_POST: dict(),
                KEY_EXPECTED_EXCEPTION: {
                    frozenset([('compress', True), ('with_chunks', False)]): {
                        'detail': {'path': 'temporary_zip_file.zip/ne_110m_admin_0_boundary_lines_land.shp'}},
                    frozenset([('compress', True), ('with_chunks', True)]): {
                        'detail': {'path': 'shp_without_prj_patch_all_files_chunks_zipped.zip/ne_110m_admin_0_boundary_lines_land.shp'}}
                },
            },
        },
    },
    'empty_zip': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [],
            'compress': True,
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'detail': {'parameter': 'file',
                                     'message': 'Zip file without data file inside.',
                                     'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                                     'files': [
                                         'temporary_zip_file.zip',
                                     ],
                                     },
                          },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
                'detail': {'files': ['empty_zip_post_chunks_zipped.zip']}}
        },
    },
    'tif_with_qml': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': ['sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif'],
            'style_file': 'sample/style/ne_10m_admin_0_countries.qml',
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 48,
                          'message': 'Wrong combination of parameters',
                          'detail': 'Raster layers are not allowed to have QML style.',
                          },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
            }
        },
        KEY_PATCHES: {
            'data_and_style': {
                KEY_PATCH_POST: dict(),
            },
            'data_without_style': {
                KEY_PATCH_POST: {
                    'file_paths': ['sample/layman.layer/sample_point_cz.geojson'],
                    'style_file': 'sample/layman.layer/sample_point_cz.qml',
                },
                KEY_ACTION_PARAMS: {
                    'style_file': None,
                },
            },
        },
    },
    'non_readable_raster': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [f'{DIRECTORY}/non_readable_raster.tif'],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'message': 'Wrong parameter value',
                          'detail': {'parameter': 'file',
                                     'message': 'Unable to open raster file.',
                                     'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                                     'file': '/layman_data_test/workspaces/dynamic_test_workspace_generated_wrong_input/layers/non_readable_raster_post_sync/input_file/non_readable_raster_post_sync.tif',
                                     },
                          },
            frozenset([('compress', True), ('with_chunks', False)]): {
                'detail': {'file': '/vsizip//layman_data_test/workspaces/dynamic_test_workspace_generated_wrong_input/layers/non_readable_raster_post_sync_zipped/input_file/non_readable_raster_post_sync_zipped.zip/non_readable_raster.tif',
                           }
            },
            frozenset([('compress', False), ('with_chunks', True)]): {
                'sync': False,
                'detail': {'file': '/layman_data_test/workspaces/dynamic_test_workspace_generated_wrong_input/layers/non_readable_raster_post_chunks/input_file/non_readable_raster_post_chunks.tif',
                           }
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
                'detail': {'file': '/vsizip//layman_data_test/workspaces/dynamic_test_workspace_generated_wrong_input/layers/non_readable_raster_post_chunks_zipped/input_file/non_readable_raster_post_chunks_zipped.zip/non_readable_raster.tif',
                           }
            },
        },
    },
    'pgw_png_unsupported_crs': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': ['sample/layman.layer/sample_png_pgw_rgba.pgw',
                           'sample/layman.layer/sample_png_pgw_rgba.png', ],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 4,
                          'message': 'Unsupported CRS of data file',
                          'detail': {'found': None, 'supported_values': settings.INPUT_SRS_LIST},
                          },
            frozenset([('compress', False), ('with_chunks', True)]): {
                'sync': False,
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
            },
        },
        KEY_PATCHES: {
            'patch': {
                KEY_PATCH_POST: publications.SMALL_LAYER.definition,
            },
        },
    },
    'png_without_pgw': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': ['sample/layman.layer/sample_png_pgw_rgba.png', ],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 4,
                          'message': 'Unsupported CRS of data file',
                          'detail': {'found': None, 'supported_values': settings.INPUT_SRS_LIST},
                          },
            frozenset([('compress', False), ('with_chunks', True)]): {
                'sync': False,
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
            },
        },
        KEY_PATCHES: {
            'patch': {
                KEY_PATCH_POST: publications.SMALL_LAYER.definition,
            },
        },
    },
    'shp_with_unsupported_epsg': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [
                f'{DIRECTORY}/sample_point_cz_2154.cpg',
                f'{DIRECTORY}/sample_point_cz_2154.dbf',
                f'{DIRECTORY}/sample_point_cz_2154.prj',
                f'{DIRECTORY}/sample_point_cz_2154.qmd',
                f'{DIRECTORY}/sample_point_cz_2154.shp',
                f'{DIRECTORY}/sample_point_cz_2154.shx',
            ],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 4,
                          'message': 'Unsupported CRS of data file',
                          'detail': {'found': 'EPSG:2154', 'supported_values': settings.INPUT_SRS_LIST},
                          },
            frozenset([('compress', False), ('with_chunks', True)]): {
                'sync': False,
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
            },
        },
        KEY_PATCHES: {
            'patch': {
                KEY_PATCH_POST: publications.SMALL_LAYER.definition,
            },
        },
    },
    'tif_with_unsupported_epsg': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [f'{DIRECTORY}/sample_tif_rgb_2154.tif', ],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 4,
                          'message': 'Unsupported CRS of data file',
                          'detail': {'found': 'EPSG:2154', 'supported_values': settings.INPUT_SRS_LIST},
                          },
            frozenset([('compress', False), ('with_chunks', True)]): {
                'sync': False,
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
            },
        },
        KEY_PATCHES: {
            'patch': {
                KEY_PATCH_POST: publications.SMALL_LAYER.definition,
            },
        },
    },
    'tif_with_unsupported_bands': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': ['sample/layman.layer/sample_tif_rg.tif', ],
            'with_chunks': False,
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'message': 'Wrong parameter value',
                          'detail': {'parameter': 'file',
                                     'expected': 'Any of color interpretations [Gray], '
                                                 '[Gray, Alpha], [Palette], [Red, Green, Blue], '
                                                 '[Red, Green, Blue, Alpha].',
                                     'found': ['Red', 'Green']
                                     },
                          },
        },
        KEY_PATCHES: {
            'patch': {
                KEY_PATCH_POST: publications.SMALL_LAYER.definition,
            },
        },
    },
    'two_main_files': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [
                'sample/layman.layer/small_layer.geojson',
                'sample/layman.layer/sample_tif_rgb.tif',
            ],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'message': 'Wrong parameter value',
                          'detail': {
                              'expected': 'At most one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or timeseries with time_regex parameter.',
                              'files': [
                                  'sample_tif_rgb.tif',
                                  'small_layer.geojson'],
                              'parameter': 'file'},
                          },
            frozenset([('compress', True), ('with_chunks', False)]): {
                'detail': {
                    'files': [
                        'temporary_zip_file.zip/sample_tif_rgb.tif',
                        'temporary_zip_file.zip/small_layer.geojson'],
                }
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
                'detail': {
                    'files': [
                        'two_main_files_post_chunks_zipped.zip/sample_tif_rgb.tif',
                        'two_main_files_post_chunks_zipped.zip/small_layer.geojson'],
                }
            },
        },
        KEY_PATCHES: {
            'patch': {
                KEY_PATCH_POST: publications.SMALL_LAYER.definition,
                KEY_ACTION_PARAMS: {},
                KEY_EXPECTED_EXCEPTION: {
                    frozenset([('compress', True), ('with_chunks', True)]): {
                        'sync': False,
                        'detail': {
                            'files': [
                                'two_main_files_patch_patch_chunks_zipped.zip/sample_tif_rgb.tif',
                                'two_main_files_patch_patch_chunks_zipped.zip/small_layer.geojson'],
                        }
                    },
                },
            },
        },
    },
    'two_zip_files': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [
                'tmp/sm5/vektor/sm5.zip',
                f'{DIRECTORY}/layer_with_two_main_files.zip',
            ],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'detail': {'parameter': 'file',
                                     'expected': 'At most one file with extensions: .zip',
                                     'files': [
                                         'sm5.zip',
                                         'layer_with_two_main_files.zip',
                                     ],
                                     },
                          },
            frozenset([('compress', True), ('with_chunks', False)]): {
                'detail': {
                    'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                    'files': [
                        'temporary_zip_file.zip/sm5.zip',
                        'temporary_zip_file.zip/layer_with_two_main_files.zip',
                    ],
                    'message': 'Zip file without data file inside.',
                    'parameter': 'file'
                }
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
                'detail': {
                    'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                    'files': [
                        'two_zip_files_post_chunks_zipped.zip/sm5.zip',
                        'two_zip_files_post_chunks_zipped.zip/layer_with_two_main_files.zip',
                    ],
                    'message': 'Zip file without data file inside.',
                    'parameter': 'file'
                }
            },
        },
        KEY_PATCHES: {
            'patch': {
                KEY_PATCH_POST: publications.SMALL_LAYER.definition,
                KEY_EXPECTED_EXCEPTION: {
                    frozenset([('compress', True), ('with_chunks', False)]): {
                        'detail': {
                            'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                            'files': [
                                'temporary_zip_file.zip/sm5.zip',
                                'temporary_zip_file.zip/layer_with_two_main_files.zip',
                            ],
                            'message': 'Zip file without data file inside.',
                            'parameter': 'file'
                        }
                    },
                    frozenset([('compress', True), ('with_chunks', True)]): {
                        'sync': False,
                        'detail': {
                            'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                            'files': [
                                'two_zip_files_patch_patch_chunks_zipped.zip/sm5.zip',
                                'two_zip_files_patch_patch_chunks_zipped.zip/layer_with_two_main_files.zip',
                            ],
                            'message': 'Zip file without data file inside.',
                            'parameter': 'file'
                        }
                    },

                },
            },
        },
    },
    'epsg_4326_en': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [
                f'{DIRECTORY}/small_layer_4326_en.shp',
                f'{DIRECTORY}/small_layer_4326_en.dbf',
                f'{DIRECTORY}/small_layer_4326_en.prj',
                f'{DIRECTORY}/small_layer_4326_en.shx',
            ],
            'compress': False,
            'with_chunks': False,
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 4,
                          'detail': {'found': None, 'supported_values': settings.INPUT_SRS_LIST},
                          },
        },
    },
    'map_schema_1_0_0': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.MAP_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [
                f'{DIRECTORY}/map_schema_1_1_0.json',
            ],
            'compress': False,
            'with_chunks': False,
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'detail': {'expected': 'JSON file according schema `https://github.com/hslayers/map-compositions`, version 2',
                                     'parameter': 'file',
                                     'reason': 'Missing key `describedBy`'},
                          },
        },
    },
    'map_schema_3_0_0': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.MAP_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [
                f'{DIRECTORY}/map_schema_3_0_0.json',
            ],
            'compress': False,
            'with_chunks': False,
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'detail': {'expected': '2.x.x',
                                     'parameter': 'file',
                                     'reason': 'Invalid schema version'},
                          },
        },
    },
    'map_unsupported_crs': {
        KEY_PUBLICATION_TYPE: process_client.MAP_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [
                f'{DIRECTORY}/map_unsupported_crs.json',
            ],
            'compress': False,
            'with_chunks': False,
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 4,
                          'detail': {'found': 'EPSG:3030',
                                     'supported_values': settings.INPUT_SRS_LIST},
                          },
        },
    },
    'layer_unsupported_overview_resampling': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': ['sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif'],
            'overview_resampling': 'no_overview_resampling',
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'detail': {'expected': 'Resampling method for gdaladdo utility, https://gdal.org/programs/gdaladdo.html',
                                     'parameter': 'overview_resampling',
                                     'detail': {'found': 'no_overview_resampling',
                                                'supported_values': settings.OVERVIEW_RESAMPLING_METHOD_LIST}, },
                          },
        },
        KEY_PATCHES: {
            'full': {
                KEY_PATCH_POST: publications.SMALL_LAYER.definition,
            },
        },
    },
    'layer_vector_overview_resampling': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'overview_resampling': 'nearest',
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 48,
                          'message': 'Wrong combination of parameters',
                          'detail': 'Vector layers do not support overview resampling.',
                          },
            frozenset([('compress', False), ('with_chunks', True)]): {
                'sync': False,
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
            },
        },
        KEY_PATCHES: {
            'full': {
                KEY_PATCH_POST: publications.SMALL_LAYER.definition,
                KEY_ACTION_PARAMS: {
                    'file_paths': ['sample/layman.layer/small_layer.geojson'],
                    'overview_resampling': 'nearest',
                },
            },
        },
    },
    'layer_overview_resampling_no_input_file': {
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
                          'detail': 'Parameter overview_resampling requires parameter file to be set.',
                          },
        },
        KEY_PATCHES: {
            'full': {
                KEY_PATCH_POST: {
                    'file_paths': ['sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif'],
                    'overview_resampling': 'nearest',
                },
                KEY_ACTION_PARAMS: {
                    'file_paths': [],
                    'overview_resampling': 'mode',
                },
                KEY_EXPECTED_EXCEPTION: {
                    frozenset([('compress', True), ('with_chunks', False)]): {
                        'code': 2,
                        'message': 'Wrong parameter value',
                        'detail': {
                            'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                            'files': ['temporary_zip_file.zip'],
                            'message': 'Zip file without data file inside.',
                            'parameter': 'file'
                        },
                    },
                    frozenset([('compress', True), ('with_chunks', True)]): {
                        'sync': False,
                        'code': 2,
                        'message': 'Wrong parameter value',
                        'detail': {
                            'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                            'files': ['layer_overview_resampling_no_input_file_patch_full_chunks_zipped.zip'],
                            'message': 'Zip file without data file inside.',
                            'parameter': 'file'
                        },
                    },
                },
            },
        },
    },
    'layer_name_211': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'name': 'a' * 211,
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'detail': {'parameter': 'layername',
                                     'detail': 'Layer name too long (211), maximum allowed length is 210.',
                                     },
                          },
        },
    },
    'map_name_211': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.MAP_TYPE,
        KEY_ACTION_PARAMS: {
            'name': 'a' * 211,
            'compress': False,
            'with_chunks': False,
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'detail': {'parameter': 'mapname',
                                     'detail': 'Map name too long (211), maximum allowed length is 210.',
                                     },
                          },
        },
    },
    'wrong_time_regex': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'time_regex': '[',
            'file_paths': [
                'tests/dynamic_data/publications/timeseries/timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
            ],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'detail': {'parameter': 'time_regex',
                                     'expected': 'Regular expression',
                                     },
                          },
        },
        KEY_PATCHES: {
            'full': {
                KEY_PATCH_POST: publications.SMALL_LAYER.definition,
            },
        },
    },
    'vector_time_regex': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'time_regex': r'[0-9]{8}T[0-9]{9}Z(\?!.\*[0-9]{8}T[0-9]{9}Z.\*)',
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 48,
                          'detail': 'Vector layers are not allowed to be combined with `time_regex` parameter.',
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
            'time_regex': r'[0-9]{8}T[0-9]{9}Z(\?!.\*[0-9]{8}T[0-9]{9}Z.\*)',
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
                          'detail': {'expected': 'All main files with the same extension.',
                                     'files': ['sample_jp2_rgb.jp2', 'single_point.shp'],
                                     'extensions': ['.jp2', '.shp'],
                                     'parameter': 'file',
                                     },
                          },
            frozenset([('compress', True), ('with_chunks', False)]): {
                'detail': {'files': ['temporary_zip_file.zip/sample_jp2_rgb.jp2', 'temporary_zip_file.zip/single_point.shp'],
                           },
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
                'detail': {'files': ['raster_vector_time_regex_post_chunks_zipped.zip/sample_jp2_rgb.jp2', 'raster_vector_time_regex_post_chunks_zipped.zip/single_point.shp'],
                           },
            },
        },
    },
    'dif_raster_types_time_regex': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'time_regex': r'[0-9]{8}T[0-9]{9}Z(\?!.\*[0-9]{8}T[0-9]{9}Z.\*)',
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
                          'detail': {'expected': 'All main files with the same extension.',
                                     'files': ['sample_jp2_j2w_rgb.jp2', 'sample_jpeg_jgw_rgb.jpeg', ],
                                     'extensions': ['.jp2', '.jpeg'],
                                     'parameter': 'file',
                                     },
                          },
            frozenset([('compress', True), ('with_chunks', False)]): {
                'detail': {'files': ['temporary_zip_file.zip/sample_jp2_j2w_rgb.jp2', 'temporary_zip_file.zip/sample_jpeg_jgw_rgb.jpeg', ],
                           },
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
                'detail': {'files': ['dif_raster_types_time_regex_post_chunks_zipped.zip/sample_jp2_j2w_rgb.jp2', 'dif_raster_types_time_regex_post_chunks_zipped.zip/sample_jpeg_jgw_rgb.jpeg', ],
                           },
            },
        },
    },
    'raster_and_zip_raster_time_regex': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'time_regex': r'[0-9]{8}T[0-9]{9}Z(\?!.\*[0-9]{8}T[0-9]{9}Z.\*)',
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
                          'detail': {'expected': 'One compressed file or one or more uncompressed files.',
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
                          'detail': {'expected': 'All main files with the same CRS.',
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
                          'detail': {'expected': 'All main files with the same color interpretations.',
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
                          'detail': {
                              'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                              'files': ['sample_jp2_j2w_rgb.j2w'],
                              'message': 'No data file in input.',
                              'parameter': 'file',
                          }
                          },
            frozenset([('compress', True), ('with_chunks', False)]): {
                'detail': {'files': ['temporary_zip_file.zip/sample_jp2_j2w_rgb.j2w'],
                           'message': 'Zip file without data file inside.', }
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
                'detail': {'files': ['non_data_file_without_data_file_post_chunks_zipped.zip/sample_jp2_j2w_rgb.j2w'],
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
                        'detail': {'files': ['non_data_file_without_data_file_patch_full_chunks_zipped.zip/sample_jp2_j2w_rgb.j2w'],
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
                          'detail': 'Parameter time_regex is allowed only in combination with files.',
                          },
        },
        KEY_PATCHES: {
            'full': {
                KEY_PATCH_POST: {
                    'time_regex': r'[0-9]{8}',
                    'file_paths': [
                        'tests/dynamic_data/publications/timeseries/timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                        'tests/dynamic_data/publications/timeseries/timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.TIF',
                    ],
                },
                KEY_ACTION_PARAMS: {
                    'time_regex': r'[0-9]{8}T[0-9]{9}Z(\?!.\*[0-9]{8}T[0-9]{9}Z.\*)',
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
                          'detail': {
                              'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg; or one of them in single .zip file.',
                              'files': ['sample_jp2_j2w_rgb.j2w'],
                              'message': 'No data file in input.',
                              'parameter': 'file',
                          }
                          },
            frozenset([('compress', True), ('with_chunks', False)]): {
                'detail': {'files': ['temporary_zip_file.zip/sample_jp2_j2w_rgb.j2w'],
                           'message': 'Zip file without data file inside.', }
            },
            frozenset([('compress', True), ('with_chunks', True)]): {
                'sync': False,
                'detail': {'files': ['time_regex_with_non_data_file_post_chunks_zipped.zip/sample_jp2_j2w_rgb.j2w'],
                           'message': 'Zip file without data file inside.', }
            },
        },
        KEY_PATCHES: {
            'full': {
                KEY_PATCH_POST: publications.SMALL_LAYER.definition,
                KEY_ACTION_PARAMS: {
                    'time_regex': r'[0-9]{8}T[0-9]{9}Z(\?!.\*[0-9]{8}T[0-9]{9}Z.\*)',
                    'file_paths': ['sample/layman.layer/sample_jp2_j2w_rgb.j2w'],
                },
                KEY_EXPECTED_EXCEPTION: {
                    frozenset([('compress', True), ('with_chunks', True)]): {
                        'detail': {'files': ['time_regex_with_non_data_file_patch_full_chunks_zipped.zip/sample_jp2_j2w_rgb.j2w'],
                                   }
                    },
                },
            },
        },
    },
    'filename_not_match_time_regex': {
        EnumTestKeys.TYPE: EnumTestTypes.OPTIONAL,
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'time_regex': r'non_existing_regex',
            'file_paths': ['tests/dynamic_data/publications/timeseries/timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif'],
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 48,
                          'message': 'Wrong combination of parameters',
                          'detail': {
                              'message': 'File does not match time_regex.',
                              'expected': 'All main data files match time_regex parameter',
                              'unmatched_filenames': ['S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif'],
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
                    'time_regex': r'non_existing_regex',
                    'file_paths': [
                        'tests/dynamic_data/publications/timeseries/timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif'],
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
                          'detail': {
                              'message': 'Too long filename in timeseries.',
                              'expected': 'All files names shorter than 211 characters',
                              'too_long_filenames': ['211_too_long_name_20220319_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.zip/211_too_long_name_20220319_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.tif'],
                          },
                          },
            frozenset([('compress', False), ('with_chunks', True)]): {
                'sync': False,
                'detail': {'too_long_filenames': ['/layman_data_test/workspaces/dynamic_test_workspace_generated_wrong_input/layers/too_long_filename_with_time_regexp_post_chunks/input_file/too_long_filename_with_time_regexp_post_chunks.zip/211_too_long_name_20220319_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.tif']}
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
                        'detail': {'too_long_filenames': ['/layman_data_test/workspaces/dynamic_test_workspace_generated_wrong_input/layers/too_long_filename_with_time_regexp_patch_full_chunks/input_file/too_long_filename_with_time_regexp_patch_full_chunks.zip/211_too_long_name_20220319_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.tif']}
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
                          'detail': {
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
                          'detail': {
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
                'tests/dynamic_data/publications/timeseries/timeseries_tif/S2A_MSIL2A_20220316T100031.0.tif'
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
}

VALIDATION_PATCH_ACTION = {
    consts.KEY_ACTION: {
        consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
            'file_paths': ['sample/layman.layer/small_layer.geojson'],
            'style_file': 'sample/style/basic.sld',
        }),
        consts.KEY_RESPONSE_ASSERTS: [
            Action(processing.response.valid_post, dict()),
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
    test_type_str = os.getenv(EnumTestKeys.TYPE.value, EnumTestTypes.MANDATORY.value)
    test_type = EnumTestTypes(test_type_str)
    default_only_first_parametrization = test_type != EnumTestTypes.OPTIONAL

    result = dict()
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
                exception_diff = tc_params[KEY_EXPECTED_EXCEPTION].get(rest_param_frozen_set, dict())
                exp_exception = asserts_util.recursive_dict_update(default_exp_exception, exception_diff)
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
                            Action(publication.internal.does_not_exist, dict())
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
                                Action(processing.response.valid_post, dict()),
                            ],
                        },
                        consts.KEY_FINAL_ASSERTS: [
                            Action(publication.rest.async_error_in_info_key, {'info_key': failed_info_key,
                                                                              'expected': exp_exception, }, ),
                        ],
                    }
                    if assert_no_bbox_and_crs:
                        action_def[consts.KEY_FINAL_ASSERTS].append(Action(publication.internal.no_bbox_and_crs, dict()))
                    action_list = [action_def, VALIDATION_PATCH_ACTION]
                publ_name = f"{testcase}_post{test_case_postfix}"
                result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], publ_name)] = action_list

        for patch_key, patch_params in tc_params.get(KEY_PATCHES, dict()).items():
            action_parametrization = util.get_test_case_parametrization(param_parametrization=REST_PARAMETRIZATION,
                                                                        only_first_parametrization=default_only_first_parametrization,
                                                                        default_params={**tc_params[KEY_ACTION_PARAMS],
                                                                                        **patch_params.get(KEY_ACTION_PARAMS, dict())},
                                                                        action_parametrization=[('', None, []), ],
                                                                        )
            for test_case_postfix, _, _, rest_param_dict in action_parametrization:
                patch = [
                    {
                        consts.KEY_ACTION: {
                            consts.KEY_CALL: Action(process_client.publish_workspace_publication,
                                                    patch_params[KEY_PATCH_POST]),
                            consts.KEY_RESPONSE_ASSERTS: [
                                Action(processing.response.valid_post, dict()),
                            ],
                        },
                        consts.KEY_FINAL_ASSERTS: [
                            *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                        ]
                    },
                ]
                rest_param_frozen_set = frozenset(rest_param_dict.items())
                default_exp_exception = copy.deepcopy(tc_params[KEY_EXPECTED_EXCEPTION][KEY_DEFAULT])
                exception_diff_post = tc_params[KEY_EXPECTED_EXCEPTION].get(rest_param_frozen_set, dict())
                exception_diff_patch = patch_params.get(KEY_EXPECTED_EXCEPTION, dict()).get(rest_param_frozen_set, dict())
                exception_diff = asserts_util.recursive_dict_update(exception_diff_post, exception_diff_patch)
                exp_exception = asserts_util.recursive_dict_update(default_exp_exception, exception_diff)
                is_sync = exp_exception.pop('sync')
                if is_sync:
                    action_def = {
                        consts.KEY_ACTION: {
                            consts.KEY_CALL: Action(process_client.patch_workspace_publication,
                                                    {**tc_params[KEY_ACTION_PARAMS],
                                                     **patch_params.get(KEY_ACTION_PARAMS, dict()),
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
                                                     **patch_params.get(KEY_ACTION_PARAMS, dict()),
                                                     **rest_param_dict}),
                            consts.KEY_RESPONSE_ASSERTS: [
                                Action(processing.response.valid_post, dict()),
                            ],
                        },
                        consts.KEY_FINAL_ASSERTS: [
                            Action(publication.rest.async_error_in_info_key, {'info_key': failed_info_key,
                                                                              'expected': exp_exception, }, ),
                        ],
                    }
                    if assert_no_bbox_and_crs:
                        action_def[consts.KEY_FINAL_ASSERTS].append(Action(publication.internal.no_bbox_and_crs, dict()))

                    patch.append(action_def)
                    patch.append(VALIDATION_PATCH_ACTION)
                publ_name = f"{testcase}_patch_{patch_key}{test_case_postfix}"
                result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], publ_name)] = patch

    return result
