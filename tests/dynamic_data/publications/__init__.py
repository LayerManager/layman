from layman import LaymanError
import tests.asserts.final.publication as publication
import tests.asserts.processing as processing
from test_tools import process_client
from . import wrong_input, file_input
from .common_layers import LAYERS
from .. import predefined_actions, predefined_zip_files
from ... import Action, Publication, dynamic_data as consts


PUBLICATIONS = {
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'basic_sld'): [
        {
            consts.KEY_ACTION: predefined_actions.POST_TIF_WITH_QML,
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, LAYERS['small_layer'].definition),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, LAYERS['small_layer'].info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': LAYERS['small_layer'].thumbnail,
                }),
            ],
        },
        {
            consts.KEY_ACTION: predefined_actions.PATCH_TIF_WITH_QML,
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, LAYERS['small_layer'].info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': LAYERS['small_layer'].thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_sld'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': ['test_tools/data/layers/layer_with_two_main_files.zip'],
                }),
                consts.KEY_CALL_EXCEPTION: {
                    consts.KEY_EXCEPTION: LaymanError,
                    consts.KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {'expected': {'http_code': 400,
                                                                                      'code': 2,
                                                                                      'message': 'Wrong parameter value',
                                                                                      'detail': {
                                                                                          'expected': 'At most one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg',
                                                                                          'files': [
                                                                                              'layer_with_two_main_files.zip/layer_with_two_main_files/geojson/small_layer.geojson',
                                                                                              'layer_with_two_main_files.zip/layer_with_two_main_files/raster/sample_tif_rgb.tif'],
                                                                                          'parameter': 'file'},
                                                                                      }, }, ),
                    ],
                },
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': [
                        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.cpg',
                        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.README.html',
                        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp',
                        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shx',
                        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.VERSION.txt',
                    ],
                    'compress': True,
                }),
                consts.KEY_CALL_EXCEPTION: {
                    consts.KEY_EXCEPTION: LaymanError,
                    consts.KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {'expected': {'http_code': 400,
                                                                                      'code': 18,
                                                                                      'message': 'Missing one or more ShapeFile files.',
                                                                                      'detail': {'missing_extensions': ['.dbf', '.prj'],
                                                                                                 'suggestion': 'Missing .prj file can be fixed also by setting "crs" parameter.',
                                                                                                 'path': 'temporary_zip_file.zip/ne_110m_admin_0_boundary_lines_land.shp',
                                                                                                 },
                                                                                      }, }, ),
                    ],
                },
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    **predefined_zip_files.SMALL_LAYER_ZIP,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    **LAYERS['small_layer'].info_values,
                    'file_extension': 'zip/small_layer.geojson',
                    'gdal_prefix': '/vsizip/',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': LAYERS['small_layer'].thumbnail,
                }),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
                    'file_paths': ['test_tools/data/layers/layer_with_two_main_files.zip'],
                }),
                consts.KEY_CALL_EXCEPTION: {
                    consts.KEY_EXCEPTION: LaymanError,
                    consts.KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {'expected': {'http_code': 400,
                                                                                      'code': 2,
                                                                                      'message': 'Wrong parameter value',
                                                                                      'detail': {
                                                                                          'expected': 'At most one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg',
                                                                                          'files': [
                                                                                              'layer_with_two_main_files.zip/layer_with_two_main_files/geojson/small_layer.geojson',
                                                                                              'layer_with_two_main_files.zip/layer_with_two_main_files/raster/sample_tif_rgb.tif'],
                                                                                          'parameter': 'file'},
                                                                                      }, }, ),
                    ],
                },
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    **LAYERS['small_layer'].info_values,
                    'file_extension': 'zip/small_layer.geojson',
                    'gdal_prefix': '/vsizip/',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': LAYERS['small_layer'].thumbnail,
                }),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
                    'file_paths': [
                        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.cpg',
                        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.README.html',
                        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp',
                        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shx',
                        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.VERSION.txt',
                    ],
                    'compress': True,
                }),
                consts.KEY_CALL_EXCEPTION: {
                    consts.KEY_EXCEPTION: LaymanError,
                    consts.KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {'expected': {'http_code': 400,
                                                                                      'code': 18,
                                                                                      'message': 'Missing one or more ShapeFile files.',
                                                                                      'detail': {'missing_extensions': ['.dbf', '.prj'],
                                                                                                 'suggestion': 'Missing .prj file can be fixed also by setting "crs" parameter.',
                                                                                                 'path': 'temporary_zip_file.zip/ne_110m_admin_0_boundary_lines_land.shp',
                                                                                                 },
                                                                                      }, }, ),
                    ],
                },
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    **LAYERS['small_layer'].info_values,
                    'file_extension': 'zip/small_layer.geojson',
                    'gdal_prefix': '/vsizip/',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': LAYERS['small_layer'].thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_shp_sld'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    **predefined_zip_files.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    **LAYERS['ne_110m_admin_0_boundary_lines_land'].info_values,
                    'file_extension': 'zip/ne_110m_admin_0_boundary lines land +ěščřžýáí/ne_110m_admin_0_boundary_lines_land ížě.shp',
                    'gdal_prefix': '/vsizip/',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': LAYERS['ne_110m_admin_0_boundary_lines_land'].thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_tif_tfw_rgba_opaque'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    **predefined_zip_files.SAMPLE_TIF_TFW_RGBA_OPAQUE,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    'exp_publication_detail': {
                        'bounding_box': [1669480.0, 6580973.000000007, 1675351.9999999802, 6586999.0],
                        'native_crs': 'EPSG:3857',
                        'native_bounding_box': [1669480.0, 6580973.000000007, 1675351.9999999802, 6586999.0, 'EPSG:3857'],
                    },
                    'file_extension': 'zip/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque.tif',
                    'gdal_prefix': '/vsizip/',
                    'publ_type_detail': ('raster', 'sld'),
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'test_tools/data/thumbnail/raster_layer_tiff.png',
                }),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
                    **predefined_zip_files.SMALL_LAYER_ZIP,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    **LAYERS['small_layer'].info_values,
                    'exp_publication_detail': {
                        **LAYERS['small_layer'].info_values['exp_publication_detail'],
                        '_file': {
                            'path': '/layman_data_test/workspaces/dynamic_test_workspace/layers/zipped_tif_tfw_rgba_opaque/input_file/zipped_tif_tfw_rgba_opaque.zip/small_layer.geojson'
                        },
                        'file': {
                            'path': 'layers/zipped_tif_tfw_rgba_opaque/input_file/zipped_tif_tfw_rgba_opaque.zip/small_layer.geojson'
                        },
                    },
                    'file_extension': 'zip/small_layer.geojson',
                    'gdal_prefix': '/vsizip/',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': LAYERS['small_layer'].thumbnail,
                }),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
                    **predefined_zip_files.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    'exp_publication_detail': {
                        'bounding_box': [868376.0, 522128.0, 940583.0, 593255.0],
                        'native_crs': 'EPSG:3857',
                        'native_bounding_box': [868376.0, 522128.0, 940583.0, 593255.0, 'EPSG:3857'],
                    },
                    'file_extension': 'zip/sample_tif_colortable_nodata_opaque/sample_tif_colortable_nodata_opaque.tif',
                    'gdal_prefix': '/vsizip/',
                    'publ_type_detail': ('raster', 'sld'),
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'test_tools/data/thumbnail/raster_layer_tif_colortable_nodata_opaque.png',
                }),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
                    **predefined_zip_files.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    **LAYERS['ne_110m_admin_0_boundary_lines_land'].info_values,
                    'file_extension': 'zip/ne_110m_admin_0_boundary lines land +ěščřžýáí/ne_110m_admin_0_boundary_lines_land ížě.shp',
                    'gdal_prefix': '/vsizip/',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': LAYERS['ne_110m_admin_0_boundary_lines_land'].thumbnail,
                }),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
                    **predefined_zip_files.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    'exp_publication_detail': {
                        'bounding_box': [868376.0, 522128.0, 940583.0, 593255.0],
                        'native_crs': 'EPSG:3857',
                        'native_bounding_box': [868376.0, 522128.0, 940583.0, 593255.0, 'EPSG:3857'],
                    },
                    'file_extension': 'zip/sample_tif_colortable_nodata_opaque/sample_tif_colortable_nodata_opaque.tif',
                    'gdal_prefix': '/vsizip/',
                    'publ_type_detail': ('raster', 'sld'),
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'test_tools/data/thumbnail/raster_layer_tif_colortable_nodata_opaque.png',
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_tif_colortable_nodata_opaque'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    **predefined_zip_files.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    'exp_publication_detail': {
                        'bounding_box': [868376.0, 522128.0, 940583.0, 593255.0],
                        'native_crs': 'EPSG:3857',
                        'native_bounding_box': [868376.0, 522128.0, 940583.0, 593255.0, 'EPSG:3857'],
                    },
                    'file_extension': 'zip/sample_tif_colortable_nodata_opaque/sample_tif_colortable_nodata_opaque.tif',
                    'gdal_prefix': '/vsizip/',
                    'publ_type_detail': ('raster', 'sld'),
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'test_tools/data/thumbnail/raster_layer_tif_colortable_nodata_opaque.png',
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_chunks_sld'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    **predefined_zip_files.SMALL_LAYER_ZIP,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    **LAYERS['small_layer'].info_values,
                    'file_extension': 'zip/small_layer.geojson',
                    'gdal_prefix': '/vsizip/',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': LAYERS['small_layer'].thumbnail,
                }),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
                    **predefined_zip_files.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    **LAYERS['ne_110m_admin_0_boundary_lines_land'].info_values,
                    'file_extension': 'zip/ne_110m_admin_0_boundary lines land +ěščřžýáí/ne_110m_admin_0_boundary_lines_land ížě.shp',
                    'gdal_prefix': '/vsizip/',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': LAYERS['ne_110m_admin_0_boundary_lines_land'].thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_chunks_shp_sld'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    **predefined_zip_files.NE_110M_ADMIN_0_BOUNDARY_LINES_LAND,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    **LAYERS['ne_110m_admin_0_boundary_lines_land'].info_values,
                    'file_extension': 'zip/ne_110m_admin_0_boundary lines land +ěščřžýáí/ne_110m_admin_0_boundary_lines_land ížě.shp',
                    'gdal_prefix': '/vsizip/',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': LAYERS['ne_110m_admin_0_boundary_lines_land'].thumbnail,
                }),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
                    **predefined_zip_files.SMALL_LAYER_ZIP,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    **LAYERS['small_layer'].info_values,
                    'file_extension': 'zip/small_layer.geojson',
                    'gdal_prefix': '/vsizip/',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': LAYERS['small_layer'].thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_chunks_tif_tfw_rgba_opaque'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    **predefined_zip_files.SAMPLE_TIF_TFW_RGBA_OPAQUE,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    'exp_publication_detail': {
                        'bounding_box': [1669480.0, 6580973.000000007, 1675351.9999999802, 6586999.0],
                        'native_crs': 'EPSG:3857',
                        'native_bounding_box': [1669480.0, 6580973.000000007, 1675351.9999999802, 6586999.0, 'EPSG:3857'],
                    },
                    'file_extension': 'zip/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque.tif',
                    'gdal_prefix': '/vsizip/',
                    'publ_type_detail': ('raster', 'sld'),
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'test_tools/data/thumbnail/raster_layer_tiff.png',
                }),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
                    **predefined_zip_files.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    'exp_publication_detail': {
                        'bounding_box': [868376.0, 522128.0, 940583.0, 593255.0],
                        'native_crs': 'EPSG:3857',
                        'native_bounding_box': [868376.0, 522128.0, 940583.0, 593255.0, 'EPSG:3857'],
                    },
                    'file_extension': 'zip/sample_tif_colortable_nodata_opaque/sample_tif_colortable_nodata_opaque.tif',
                    'gdal_prefix': '/vsizip/',
                    'publ_type_detail': ('raster', 'sld'),
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'test_tools/data/thumbnail/raster_layer_tif_colortable_nodata_opaque.png',
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_chunks_tif_colortable_nodata_opaque'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    **predefined_zip_files.SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    'exp_publication_detail': {
                        'bounding_box': [868376.0, 522128.0, 940583.0, 593255.0],
                        'native_crs': 'EPSG:3857',
                        'native_bounding_box': [868376.0, 522128.0, 940583.0, 593255.0, 'EPSG:3857'],
                    },
                    'file_extension': 'zip/sample_tif_colortable_nodata_opaque/sample_tif_colortable_nodata_opaque.tif',
                    'gdal_prefix': '/vsizip/',
                    'publ_type_detail': ('raster', 'sld'),
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'test_tools/data/thumbnail/raster_layer_tif_colortable_nodata_opaque.png',
                }),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
                    **predefined_zip_files.SAMPLE_TIF_TFW_RGBA_OPAQUE,
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    'exp_publication_detail': {
                        'bounding_box': [1669480.0, 6580973.000000007, 1675351.9999999802, 6586999.0],
                        'native_crs': 'EPSG:3857',
                        'native_bounding_box': [1669480.0, 6580973.000000007, 1675351.9999999802, 6586999.0, 'EPSG:3857'],
                    },
                    'file_extension': 'zip/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque.tif',
                    'gdal_prefix': '/vsizip/',
                    'publ_type_detail': ('raster', 'sld'),
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'test_tools/data/thumbnail/raster_layer_tiff.png',
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_shp_without_prj'): [
        {
            consts.KEY_ACTION: predefined_actions.POST_ZIP_SHP_WITHOUT_PRJ,
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        },
        {
            consts.KEY_ACTION: predefined_actions.POST_ZIP_SHP_WITHOUT_PRJ_WITH_CRS,
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    **LAYERS['ne_110m_admin_0_boundary_lines_land'].info_values,
                    'file_extension': 'zip/ne_110m_admin_0_boundary_lines_land.shp',
                    'gdal_prefix': '/vsizip/',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': LAYERS['ne_110m_admin_0_boundary_lines_land'].thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'png_without_pgw'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': [
                        'sample/layman.layer/sample_png_pgw_rgba.png',
                    ],
                }),
                consts.KEY_CALL_EXCEPTION: {
                    consts.KEY_EXCEPTION: LaymanError,
                    consts.KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {'expected': {'http_code': 400,
                                                                                      'code': 4,
                                                                                      'message': 'Unsupported CRS of data file',
                                                                                      'detail': {
                                                                                          'found': None,
                                                                                          'supported_values': ['EPSG:3857', 'EPSG:4326']
                                                                                      }, }, }, ),
                    ],
                },
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_png_without_pgw'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': [
                        'sample/layman.layer/sample_png_pgw_rgba.png',
                    ],
                    'compress': True,
                }),
                consts.KEY_CALL_EXCEPTION: {
                    consts.KEY_EXCEPTION: LaymanError,
                    consts.KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {'expected': {'http_code': 400,
                                                                                      'code': 4,
                                                                                      'message': 'Unsupported CRS of data file',
                                                                                      'detail': {
                                                                                          'found': None,
                                                                                          'supported_values': ['EPSG:3857', 'EPSG:4326']
                                                                                      }, }, }, ),
                    ],
                },
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'png_without_aux'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': [
                        'sample/layman.layer/sample_png_aux_rgba.png',
                    ],
                }),
                consts.KEY_CALL_EXCEPTION: {
                    consts.KEY_EXCEPTION: LaymanError,
                    consts.KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {'expected': {'http_code': 400,
                                                                                      'code': 4,
                                                                                      'message': 'Unsupported CRS of data file',
                                                                                      'detail': {
                                                                                          'found': None,
                                                                                          'supported_values': ['EPSG:3857', 'EPSG:4326']
                                                                                      }, }, }, ),
                    ],
                },
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_png_without_aux'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': [
                        'sample/layman.layer/sample_png_aux_rgba.png',
                    ],
                    'compress': True,
                }),
                consts.KEY_CALL_EXCEPTION: {
                    consts.KEY_EXCEPTION: LaymanError,
                    consts.KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {'expected': {'http_code': 400,
                                                                                      'code': 4,
                                                                                      'message': 'Unsupported CRS of data file',
                                                                                      'detail': {
                                                                                          'found': None,
                                                                                          'supported_values': ['EPSG:3857', 'EPSG:4326']
                                                                                      }, }, }, ),
                    ],
                },
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'shp_with_unsupported_epsg'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': [
                        'tmp/data200/trans/jtsk/TRANS/AirfldA.cpg',
                        'tmp/data200/trans/jtsk/TRANS/AirfldA.dbf',
                        'tmp/data200/trans/jtsk/TRANS/AirfldA.prj',
                        'tmp/data200/trans/jtsk/TRANS/AirfldA.sbn',
                        'tmp/data200/trans/jtsk/TRANS/AirfldA.shp',
                        'tmp/data200/trans/jtsk/TRANS/AirfldA.shx',
                    ],
                }),
                consts.KEY_CALL_EXCEPTION: {
                    consts.KEY_EXCEPTION: LaymanError,
                    consts.KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {'expected': {'http_code': 400,
                                                                                      'code': 4,
                                                                                      'message': 'Unsupported CRS of data file',
                                                                                      'detail': {
                                                                                          'found': 'EPSG:5514',
                                                                                          'supported_values': ['EPSG:3857', 'EPSG:4326']
                                                                                      }, }, }, ),
                    ],
                },
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_shp_with_unsupported_epsg'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': [
                        'tmp/data200/trans/jtsk/TRANS/AirfldA.cpg',
                        'tmp/data200/trans/jtsk/TRANS/AirfldA.dbf',
                        'tmp/data200/trans/jtsk/TRANS/AirfldA.prj',
                        'tmp/data200/trans/jtsk/TRANS/AirfldA.sbn',
                        'tmp/data200/trans/jtsk/TRANS/AirfldA.shp',
                        'tmp/data200/trans/jtsk/TRANS/AirfldA.shx',
                    ],
                    'compress': True,
                }),
                consts.KEY_CALL_EXCEPTION: {
                    consts.KEY_EXCEPTION: LaymanError,
                    consts.KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {'expected': {'http_code': 400,
                                                                                      'code': 4,
                                                                                      'message': 'Unsupported CRS of data file',
                                                                                      'detail': {
                                                                                          'found': 'EPSG:5514',
                                                                                          'supported_values': ['EPSG:3857', 'EPSG:4326']
                                                                                      }, }, }, ),
                    ],
                },
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'tif_with_unsupported_epsg'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': [
                        'sample/layman.layer/sample_tif_rgb_5514.tif',
                    ],
                }),
                consts.KEY_CALL_EXCEPTION: {
                    consts.KEY_EXCEPTION: LaymanError,
                    consts.KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {'expected': {'http_code': 400,
                                                                                      'code': 4,
                                                                                      'message': 'Unsupported CRS of data file',
                                                                                      'detail': {
                                                                                          'found': 'EPSG:5514',
                                                                                          'supported_values': ['EPSG:3857', 'EPSG:4326']
                                                                                      }, }, }, ),
                    ],
                },
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_tif_with_unsupported_epsg'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': [
                        'sample/layman.layer/sample_tif_rgb_5514.tif',
                    ],
                    'compress': True,
                }),
                consts.KEY_CALL_EXCEPTION: {
                    consts.KEY_EXCEPTION: LaymanError,
                    consts.KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {'expected': {'http_code': 400,
                                                                                      'code': 4,
                                                                                      'message': 'Unsupported CRS of data file',
                                                                                      'detail': {
                                                                                          'found': 'EPSG:5514',
                                                                                          'supported_values': ['EPSG:3857', 'EPSG:4326']
                                                                                      }, }, }, ),
                    ],
                },
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'tif_with_unsupported_bands'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': [
                        'sample/layman.layer/sample_tif_rg.tif',
                    ],
                }),
                consts.KEY_CALL_EXCEPTION: {
                    consts.KEY_EXCEPTION: LaymanError,
                    consts.KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {'expected': {'http_code': 400,
                                                                                      'code': 2,
                                                                                      'detail': {'parameter': 'file',
                                                                                                 'expected': 'Any of color interpretations [Gray], '
                                                                                                             '[Gray, Alpha], [Palette], [Red, Green, Blue], '
                                                                                                             '[Red, Green, Blue, Alpha].',
                                                                                                 'found': ['Red', 'Green']
                                                                                                 }, }, }, ),
                    ],
                },
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_tif_with_unsupported_bands'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': [
                        'sample/layman.layer/sample_tif_rg.tif',
                    ],
                    'compress': True,
                }),
                consts.KEY_CALL_EXCEPTION: {
                    consts.KEY_EXCEPTION: LaymanError,
                    consts.KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {'expected': {'http_code': 400,
                                                                                      'code': 2,
                                                                                      'detail': {'parameter': 'file',
                                                                                                 'expected': 'Any of color interpretations [Gray], '
                                                                                                             '[Gray, Alpha], [Palette], [Red, Green, Blue], '
                                                                                                             '[Red, Green, Blue, Alpha].',
                                                                                                 'found': ['Red', 'Green']
                                                                                                 }, }, }, ),
                    ],
                },
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_chunks_checks'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': ['test_tools/data/layers/layer_with_two_main_files.zip'],
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.rest.async_error_in_info_key, {
                    'info_key': 'file',
                    'expected': {'code': 2,
                                 'detail': {'expected': 'At most one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg',
                                            'files': ['zipped_chunks_checks.zip/layer_with_two_main_files/geojson/small_layer.geojson',
                                                      'zipped_chunks_checks.zip/layer_with_two_main_files/raster/sample_tif_rgb.tif'],
                                            'parameter': 'file'},
                                 'message': 'Wrong parameter value'}
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'two_zip_files'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': [
                        'tmp/sm5/vektor/sm5.zip',
                        'test_tools/data/layers/layer_with_two_main_files.zip',
                    ],
                }),
                consts.KEY_CALL_EXCEPTION: {
                    consts.KEY_EXCEPTION: LaymanError,
                    consts.KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {
                            'expected': {'http_code': 400,
                                         'code': 2,
                                         'detail': {'parameter': 'file',
                                                    'expected': 'At most one file with extensions: .zip',
                                                    'files': [
                                                        'sm5.zip',
                                                        'layer_with_two_main_files.zip',
                                                    ],
                                                    }, }, }, ),
                    ],
                },
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_two_zip_files'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': [
                        'tmp/sm5/vektor/sm5.zip',
                        'test_tools/data/layers/layer_with_two_main_files.zip',
                    ],
                    'compress': True,
                }),
                consts.KEY_CALL_EXCEPTION: {
                    consts.KEY_EXCEPTION: LaymanError,
                    consts.KEY_EXCEPTION_ASSERTS: [
                        Action(processing.exception.response_exception, {
                            'expected': {'http_code': 400,
                                         'code': 2,
                                         'detail': {'parameter': 'file',
                                                    'message': 'Zip file without data file inside.',
                                                    'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg; or one of them in single .zip file.',
                                                    'files': [
                                                        'temporary_zip_file.zip/sm5.zip',
                                                        'temporary_zip_file.zip/layer_with_two_main_files.zip',
                                                    ],
                                                    }, }, }, ),
                    ],
                },
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.does_not_exist, dict())
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zip_and_main_file'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': [
                        'tmp/sm5/vektor/sm5.zip',
                        'sample/layman.layer/small_layer.geojson',
                    ],
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, LAYERS['small_layer'].info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': LAYERS['small_layer'].thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zipped_zip_and_main_file'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': [
                        'tmp/sm5/vektor/sm5.zip',
                        'sample/layman.layer/small_layer.geojson',
                    ],
                    'compress': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    **LAYERS['small_layer'].info_values,
                    'file_extension': 'zip/small_layer.geojson',
                    'gdal_prefix': '/vsizip/',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': LAYERS['small_layer'].thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'without_explicit_name'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'name': None,
                    'file_paths': ['sample/layman.layer/small_layer.geojson'],
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, {'name': 'small_layer'}),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.source_has_its_key_or_it_is_empty, {'name': 'small_layer'}),
                Action(publication.internal.source_internal_keys_are_subset_of_source_sibling_keys, {'name': 'small_layer'}),
                Action(publication.internal_rest.same_title_in_source_and_rest_multi, {'name': 'small_layer'}),
                Action(publication.internal_rest.same_values_in_internal_and_rest, {'name': 'small_layer'}),
                Action(publication.rest.is_in_rest_multi, {'name': 'small_layer'}),
                Action(publication.rest.correct_url_in_rest_multi, {'name': 'small_layer'}),
                Action(publication.internal.same_value_of_key_in_all_sources, {'name': 'small_layer'}),
                Action(publication.internal.mandatory_keys_in_all_sources, {'name': 'small_layer'}),
                Action(publication.internal.metadata_key_sources_do_not_contain_other_keys, {'name': 'small_layer'}),
                Action(publication.internal.thumbnail_key_sources_do_not_contain_other_keys, {'name': 'small_layer'}),
                Action(publication.internal.mandatory_keys_in_primary_db_schema_of_actor, {'name': 'small_layer'}),
                Action(publication.internal.other_keys_not_in_primary_db_schema_of_actor, {'name': 'small_layer'}),
                Action(publication.internal.mandatory_keys_in_all_sources_of_actor, {'name': 'small_layer'}),
                Action(publication.rest.is_complete_in_rest, {'name': 'small_layer'}),
                Action(publication.rest.mandatory_keys_in_rest, {'name': 'small_layer'}),
                Action(publication.geoserver.workspace_wms_1_3_0_capabilities_available, {'name': 'small_layer'}),
                Action(publication.geoserver.workspace_wfs_2_0_0_capabilities_available_if_vector, {'name': 'small_layer'}),
                Action(publication.internal.correct_values_in_detail, {
                    **LAYERS['small_layer'].info_values,
                    'name': 'small_layer',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'name': 'small_layer',
                    'exp_thumbnail': LAYERS['small_layer'].thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zip_without_explicit_name'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'name': None,
                    'file_paths': ['sample/layman.layer/small_layer_with_id.geojson'],
                    'compress': True,
                    'compress_settings': process_client.CompressTypeDef(archive_name='small_zip_layer'),
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, {'name': 'small_layer_with_id'}),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.source_has_its_key_or_it_is_empty, {'name': 'small_layer_with_id'}),
                Action(publication.internal.source_internal_keys_are_subset_of_source_sibling_keys, {'name': 'small_layer_with_id'}),
                Action(publication.internal_rest.same_title_in_source_and_rest_multi, {'name': 'small_layer_with_id'}),
                Action(publication.internal_rest.same_values_in_internal_and_rest, {'name': 'small_layer_with_id'}),
                Action(publication.rest.is_in_rest_multi, {'name': 'small_layer_with_id'}),
                Action(publication.rest.correct_url_in_rest_multi, {'name': 'small_layer_with_id'}),
                Action(publication.internal.same_value_of_key_in_all_sources, {'name': 'small_layer_with_id'}),
                Action(publication.internal.mandatory_keys_in_all_sources, {'name': 'small_layer_with_id'}),
                Action(publication.internal.metadata_key_sources_do_not_contain_other_keys, {'name': 'small_layer_with_id'}),
                Action(publication.internal.thumbnail_key_sources_do_not_contain_other_keys, {'name': 'small_layer_with_id'}),
                Action(publication.internal.mandatory_keys_in_primary_db_schema_of_actor, {'name': 'small_layer_with_id'}),
                Action(publication.internal.other_keys_not_in_primary_db_schema_of_actor, {'name': 'small_layer_with_id'}),
                Action(publication.internal.mandatory_keys_in_all_sources_of_actor, {'name': 'small_layer_with_id'}),
                Action(publication.rest.is_complete_in_rest, {'name': 'small_layer_with_id'}),
                Action(publication.rest.mandatory_keys_in_rest, {'name': 'small_layer_with_id'}),
                Action(publication.geoserver.workspace_wms_1_3_0_capabilities_available, {'name': 'small_layer_with_id'}),
                Action(publication.geoserver.workspace_wfs_2_0_0_capabilities_available_if_vector, {'name': 'small_layer_with_id'}),
                Action(publication.internal.correct_values_in_detail, {
                    **LAYERS['small_layer'].info_values,
                    'name': 'small_layer_with_id',
                    'file_extension': 'zip/small_layer_with_id.geojson',
                    'gdal_prefix': '/vsizip/',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'name': 'small_layer_with_id',
                    'exp_thumbnail': LAYERS['small_layer'].thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'zip_chunks_without_explicit_name'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'name': None,
                    'file_paths': ['sample/layman.layer/small_layer.geojson'],
                    'compress': True,
                    'compress_settings': process_client.CompressTypeDef(archive_name='small_zip_layer'),
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, {'name': 'small_zip_layer'}),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.internal.source_has_its_key_or_it_is_empty, {'name': 'small_zip_layer'}),
                Action(publication.internal.source_internal_keys_are_subset_of_source_sibling_keys, {'name': 'small_zip_layer'}),
                Action(publication.internal_rest.same_title_in_source_and_rest_multi, {'name': 'small_zip_layer'}),
                Action(publication.internal_rest.same_values_in_internal_and_rest, {'name': 'small_zip_layer'}),
                Action(publication.rest.is_in_rest_multi, {'name': 'small_zip_layer'}),
                Action(publication.rest.correct_url_in_rest_multi, {'name': 'small_zip_layer'}),
                Action(publication.internal.same_value_of_key_in_all_sources, {'name': 'small_zip_layer'}),
                Action(publication.internal.mandatory_keys_in_all_sources, {'name': 'small_zip_layer'}),
                Action(publication.internal.metadata_key_sources_do_not_contain_other_keys, {'name': 'small_zip_layer'}),
                Action(publication.internal.thumbnail_key_sources_do_not_contain_other_keys, {'name': 'small_zip_layer'}),
                Action(publication.internal.mandatory_keys_in_primary_db_schema_of_actor, {'name': 'small_zip_layer'}),
                Action(publication.internal.other_keys_not_in_primary_db_schema_of_actor, {'name': 'small_zip_layer'}),
                Action(publication.internal.mandatory_keys_in_all_sources_of_actor, {'name': 'small_zip_layer'}),
                Action(publication.rest.is_complete_in_rest, {'name': 'small_zip_layer'}),
                Action(publication.rest.mandatory_keys_in_rest, {'name': 'small_zip_layer'}),
                Action(publication.geoserver.workspace_wms_1_3_0_capabilities_available, {'name': 'small_zip_layer'}),
                Action(publication.geoserver.workspace_wfs_2_0_0_capabilities_available_if_vector, {'name': 'small_zip_layer'}),
                Action(publication.internal.correct_values_in_detail, {
                    **LAYERS['small_layer'].info_values,
                    'name': 'small_zip_layer',
                    'file_extension': 'zip/small_layer.geojson',
                    'gdal_prefix': '/vsizip/',
                }),
                Action(publication.internal.thumbnail_equals, {
                    'name': 'small_zip_layer',
                    'exp_thumbnail': LAYERS['small_layer'].thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'patch_posted_layer_not_in_gs_wms_workspace'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, dict()),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, LAYERS['small_layer'].info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': LAYERS['small_layer'].thumbnail,
                }),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
                    'file_paths': ['test_tools/data/layers/non_readable_raster.tif'],
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.rest.async_error_in_info_key, {'info_key': 'file',
                                                                  'expected': {'http_code': 400,
                                                                               'code': 2,
                                                                               'message': 'Wrong parameter value',
                                                                               'detail': {'parameter': 'file',
                                                                                          'message': 'Unable to open raster file.',
                                                                                          'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg; or one of them in single .zip file.',
                                                                                          'file': '/layman_data_test/workspaces/dynamic_test_workspace/layers/patch_posted_layer_not_in_gs_wms_workspace/input_file/patch_posted_layer_not_in_gs_wms_workspace.tif',
                                                                                          },
                                                                               }, }, ),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
                    'file_paths': ['sample/layman.layer/small_layer.geojson'],
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, LAYERS['small_layer'].info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': LAYERS['small_layer'].thumbnail,
                }),
            ],
        },
    ],
    Publication(consts.COMMON_WORKSPACE, consts.LAYER_TYPE, 'patch_layer_not_in_gs_wms_workspace'): [
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                    'file_paths': ['test_tools/data/layers/non_readable_raster.tif'],
                    'with_chunks': True,
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                Action(publication.rest.async_error_in_info_key, {'info_key': 'file',
                                                                  'expected': {'http_code': 400,
                                                                               'code': 2,
                                                                               'message': 'Wrong parameter value',
                                                                               'detail': {'parameter': 'file',
                                                                                          'message': 'Unable to open raster file.',
                                                                                          'expected': 'At least one file with any of extensions: .geojson, .shp, .tiff, .tif, .jp2, .png, .jpg; or one of them in single .zip file.',
                                                                                          'file': '/layman_data_test/workspaces/dynamic_test_workspace/layers/patch_layer_not_in_gs_wms_workspace/input_file/patch_layer_not_in_gs_wms_workspace.tif',
                                                                                          },
                                                                               }, }, ),
            ],
        },
        {
            consts.KEY_ACTION: {
                consts.KEY_CALL: Action(process_client.patch_workspace_publication, {
                    'file_paths': ['sample/layman.layer/small_layer.geojson'],
                }),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, LAYERS['small_layer'].info_values),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': LAYERS['small_layer'].thumbnail,
                }),
            ],
        },
    ],
    **wrong_input.generate(consts.COMMON_WORKSPACE + '_generated_wrong_input'),
    **file_input.generate(consts.COMMON_WORKSPACE + '_generated_file_input'),
}

# pylint: disable=unnecessary-comprehension
PUBLICATIONS = {
    publ: definition
    for publ, definition in PUBLICATIONS.items()
    # if publ.workspace == consts.COMMON_WORKSPACE
    #    and publ.name in ('zipped_tif_tfw_rgba_opaque')
}
