from layman import LaymanError
import tests.asserts.final.publication as publication
import tests.asserts.processing as processing
from test_tools import process_client
from . import predefined_actions, predefined_zip_files
from .. import Action, Publication, dynamic_data as consts


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
                consts.KEY_CALL: Action(process_client.publish_workspace_publication, dict()),
                consts.KEY_RESPONSE_ASSERTS: [
                    Action(processing.response.valid_post, dict()),
                ],
            },
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    'exp_publication_detail': {
                        'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699],
                    },
                    'file_extension': 'geojson',
                    'publ_type_detail': ('vector', 'sld'),
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'sample/style/basic_sld.png',
                }),
            ],
        },
        {
            consts.KEY_ACTION: predefined_actions.PATCH_TIF_WITH_QML,
            consts.KEY_FINAL_ASSERTS: [
                *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                Action(publication.internal.correct_values_in_detail, {
                    'exp_publication_detail': {
                        'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699],
                    },
                    'file_extension': 'geojson',
                    'publ_type_detail': ('vector', 'sld'),
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'sample/style/basic_sld.png',
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
                    'exp_publication_detail': {
                        'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699],
                    },
                    'file_extension': 'zip/small_layer.geojson',
                    'gdal_prefix': '/vsizip/',
                    'publ_type_detail': ('vector', 'sld'),
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'sample/style/basic_sld.png',
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
                    'exp_publication_detail': {
                        'bounding_box': [-15695801.072582014, -7341864.739114417, 15699816.562538767, 11122367.192100529],
                    },
                    'file_extension': 'zip/ne_110m_admin_0_boundary lines land +ěščřžýáí/ne_110m_admin_0_boundary_lines_land ížě.shp',
                    'gdal_prefix': '/vsizip/',
                    'publ_type_detail': ('vector', 'sld'),
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'test_tools/data/thumbnail/ne_110m_admin_0_boundary_lines_land.png',
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
                    'exp_publication_detail': {
                        'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699],
                        '_file': {
                            'path': '/layman_data_test/workspaces/dynamic_test_workspace/layers/zipped_tif_tfw_rgba_opaque/input_file/zipped_tif_tfw_rgba_opaque.zip/small_layer.geojson'
                        },
                        'file': {
                            'path': 'layers/zipped_tif_tfw_rgba_opaque/input_file/zipped_tif_tfw_rgba_opaque.zip/small_layer.geojson'
                        },
                    },
                    'file_extension': 'zip/small_layer.geojson',
                    'gdal_prefix': '/vsizip/',
                    'publ_type_detail': ('vector', 'sld'),
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'sample/style/basic_sld.png',
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
                    'exp_publication_detail': {
                        'bounding_box': [-15695801.072582014, -7341864.739114417, 15699816.562538767, 11122367.192100529],
                    },
                    'file_extension': 'zip/ne_110m_admin_0_boundary lines land +ěščřžýáí/ne_110m_admin_0_boundary_lines_land ížě.shp',
                    'gdal_prefix': '/vsizip/',
                    'publ_type_detail': ('vector', 'sld'),
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'test_tools/data/thumbnail/ne_110m_admin_0_boundary_lines_land.png',
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
                    'exp_publication_detail': {
                        'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699],
                    },
                    'file_extension': 'zip/small_layer.geojson',
                    'gdal_prefix': '/vsizip/',
                    'publ_type_detail': ('vector', 'sld'),
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'sample/style/basic_sld.png',
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
                    'exp_publication_detail': {
                        'bounding_box': [-15695801.072582014, -7341864.739114417, 15699816.562538767, 11122367.192100529],
                    },
                    'file_extension': 'zip/ne_110m_admin_0_boundary lines land +ěščřžýáí/ne_110m_admin_0_boundary_lines_land ížě.shp',
                    'gdal_prefix': '/vsizip/',
                    'publ_type_detail': ('vector', 'sld'),
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'test_tools/data/thumbnail/ne_110m_admin_0_boundary_lines_land.png',
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
                    'exp_publication_detail': {
                        'bounding_box': [-15695801.072582014, -7341864.739114417, 15699816.562538767, 11122367.192100529],
                    },
                    'file_extension': 'zip/ne_110m_admin_0_boundary lines land +ěščřžýáí/ne_110m_admin_0_boundary_lines_land ížě.shp',
                    'gdal_prefix': '/vsizip/',
                    'publ_type_detail': ('vector', 'sld'),
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'test_tools/data/thumbnail/ne_110m_admin_0_boundary_lines_land.png',
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
                    'exp_publication_detail': {
                        'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699],
                    },
                    'file_extension': 'zip/small_layer.geojson',
                    'gdal_prefix': '/vsizip/',
                    'publ_type_detail': ('vector', 'sld'),
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'sample/style/basic_sld.png',
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
                    'exp_publication_detail': {
                        'bounding_box': [-15695801.072582014, -7341864.739114417, 15699816.562538767, 11122367.192100529],
                    },
                    'file_extension': 'zip/ne_110m_admin_0_boundary_lines_land.shp',
                    'gdal_prefix': '/vsizip/',
                    'publ_type_detail': ('vector', 'sld'),
                }),
                Action(publication.internal.thumbnail_equals, {
                    'exp_thumbnail': 'test_tools/data/thumbnail/ne_110m_admin_0_boundary_lines_land.png',
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
                                                                                          'found': 'None',
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
                                                                                          'found': 'None',
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
                                                                                          'found': 'None',
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
                                                                                          'found': 'None',
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
}
