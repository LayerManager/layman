import copy
import os

from layman import LaymanError, settings
from tests.asserts import util as asserts_util
import tests.asserts.processing as processing
import tests.asserts.final.publication as publication
from test_tools import process_client, util
from .. import common_publications as publications
from .... import Action, Publication, dynamic_data as consts, TestTypes, TestKeys

KEY_PUBLICATION_TYPE = 'publ_type'
KEY_ACTION_PARAMS = 'action_params'
KEY_EXPECTED_EXCEPTION = 'expected_exception'
KEY_DEFAULT = 'default'
KEY_PATCHES = 'patches'
KEY_PATCH_POST = 'post_params'
KEY_ONLY_FIRST_PARAMETRIZATION = 'only_first_parametrization'

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

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
    'two_main_files_compressed': {
        KEY_PUBLICATION_TYPE: process_client.LAYER_TYPE,
        KEY_ACTION_PARAMS: {
            'file_paths': [f'{DIRECTORY}/layer_with_two_main_files.zip'],
            'compress': False,
        },
        consts.KEY_EXCEPTION: LaymanError,
        KEY_EXPECTED_EXCEPTION: {
            KEY_DEFAULT: {'http_code': 400,
                          'sync': True,
                          'code': 2,
                          'message': 'Wrong parameter value',
                          'detail': {
                              'expected': 'At most one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg, .jpeg',
                              'files': [
                                  'layer_with_two_main_files.zip/layer_with_two_main_files/geojson/small_layer.geojson',
                                  'layer_with_two_main_files.zip/layer_with_two_main_files/raster/sample_tif_rgb.tif'],
                              'parameter': 'file'},
                          },
            frozenset([('compress', False), ('with_chunks', True)]): {
                'sync': False,
                'detail': {
                    'files': [
                        'two_main_files_compressed_post_chunks.zip/layer_with_two_main_files/geojson/small_layer.geojson',
                        'two_main_files_compressed_post_chunks.zip/layer_with_two_main_files/raster/sample_tif_rgb.tif'],
                }
            },
        },
        KEY_PATCHES: {
            'patch': {
                KEY_PATCH_POST: publications.SMALL_LAYER.definition,
                KEY_ACTION_PARAMS: {
                    'compress': False,
                },
                KEY_EXPECTED_EXCEPTION: {
                    frozenset([('compress', False), ('with_chunks', True)]): {
                        'detail': {
                            'files': [
                                'two_main_files_compressed_patch_patch_chunks.zip/layer_with_two_main_files/geojson/small_layer.geojson',
                                'two_main_files_compressed_patch_patch_chunks.zip/layer_with_two_main_files/raster/sample_tif_rgb.tif'],
                        }
                    },
                },
            },
        },
    },
    'two_zip_files': {
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
    'layer_name_211': {
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
        KEY_PUBLICATION_TYPE: process_client.MAP_TYPE,
        KEY_ACTION_PARAMS: {
            'name': 'a' * 211,
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
    test_type_str = os.getenv(TestKeys.TYPE.value, TestTypes.MANDATORY.value)
    test_type = TestTypes(test_type_str)
    default_only_first_parametrization = test_type != TestTypes.OPTIONAL

    result = dict()
    for testcase, tc_params in TESTCASES.items():
        action_parametrization = util.get_test_case_parametrization(param_parametrization=REST_PARAMETRIZATION,
                                                                    only_first_parametrization=tc_params.get(
                                                                        KEY_ONLY_FIRST_PARAMETRIZATION, default_only_first_parametrization),
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
                        Action(publication.rest.async_error_in_info_key, {'info_key': 'file',
                                                                          'expected': exp_exception, }, ),
                        Action(publication.internal.no_bbox_and_crs, dict()),
                    ],
                }
                action_list = [action_def, VALIDATION_PATCH_ACTION]
            publ_name = f"{testcase}_post{test_case_postfix}"
            result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], publ_name)] = action_list

        for patch_key, patch_params in tc_params.get(KEY_PATCHES, dict()).items():
            action_parametrization = util.get_test_case_parametrization(param_parametrization=REST_PARAMETRIZATION,
                                                                        only_first_parametrization=tc_params.get(
                                                                            KEY_ONLY_FIRST_PARAMETRIZATION, default_only_first_parametrization),
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
                            Action(publication.rest.async_error_in_info_key, {'info_key': 'file',
                                                                              'expected': exp_exception, }, ),
                            Action(publication.internal.no_bbox_and_crs, dict()),
                        ],
                    }
                    patch.append(action_def)
                    patch.append(VALIDATION_PATCH_ACTION)
                publ_name = f"{testcase}_patch_{patch_key}{test_case_postfix}"
                result[Publication(workspace, tc_params[KEY_PUBLICATION_TYPE], publ_name)] = patch

    return result
