import tests.asserts.final.publication as publication
import tests.asserts.processing as processing
from test_tools import process_client
from . import predefined_actions
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
                    'file_paths': ['sample/layman.layer/small_layer.zip'],
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
                    'file_paths': ['sample/layman.layer/ne_110m_admin_0_boundary lines land +ěščřžýáí.zip'],
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
                    'file_extension': 'zip/ne_110m_admin_0_boundary lines land +ěščřžýáí/ne_110m_admin 0 boundary_lines_land ížě.shp',
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
                    'file_paths': ['sample/layman.layer/sample_tif_tfw_rgba_opaque.zip'],
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
                    'file_paths': ['sample/layman.layer/small_layer.zip'],
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
                    'file_paths': ['sample/layman.layer/sample_tif_colortable_nodata_opaque.zip'],
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
                    'file_paths': ['sample/layman.layer/ne_110m_admin_0_boundary lines land +ěščřžýáí.zip'],
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
                    'file_extension': 'zip/ne_110m_admin_0_boundary lines land +ěščřžýáí/ne_110m_admin 0 boundary_lines_land ížě.shp',
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
                    'file_paths': ['sample/layman.layer/sample_tif_colortable_nodata_opaque.zip'],
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
                    'file_paths': ['sample/layman.layer/sample_tif_colortable_nodata_opaque.zip'],
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
                    'file_paths': ['sample/layman.layer/small_layer.zip'],
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
}
