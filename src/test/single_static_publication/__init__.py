from test_tools import process_client

COMMON_WORKSPACE = 'test_workspace'

LAYER_TYPE = process_client.LAYER_TYPE
DEFINITION = 'definition'
TEST_DATA = 'test_data'


PUBLICATIONS = {
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_common_sld'): {
        DEFINITION: [
            {},
        ],
        TEST_DATA: {
            'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
            'file_type': 'vector',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'patch_3355bbox_sld'): {
        DEFINITION: [
            {},
            {'file_paths': ['test_tools/data/bbox/layer_3_3-5_5.geojson', ]},
        ],
        TEST_DATA: {
            'bbox': (3000, 3000, 5000, 5000),
            'file_type': 'vector',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_jp2'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_jp2_rgb.jp2', ]},
        ],
        TEST_DATA: {
            'bbox': (1829708, 6308828.600, 1833166.200, 6310848.600),
            'file_extensions': ['.jp2'],
            'normalized_color_interp': ['Red', 'Green', 'Blue'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_jp2.png',
            'file_type': 'raster',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'patch_jp2'): {
        DEFINITION: [
            dict(),
            {'file_paths': ['sample/layman.layer/sample_jp2_rgb.jp2', ]},
        ],
        TEST_DATA: {
            'bbox': (1829708, 6308828.600, 1833166.200, 6310848.600),
            'file_extensions': ['.jp2'],
            'normalized_color_interp': ['Red', 'Green', 'Blue'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_jp2.png',
            'file_type': 'raster',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_tif_rgb'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_tif_rgb.tif', ]},
        ],
        TEST_DATA: {
            'bbox': (1679391.080, 6562360.440, 1679416.230, 6562381.790),
            'file_extensions': ['.tif'],
            'normalized_color_interp': ['Red', 'Green', 'Blue'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_tif.png',
            'file_type': 'raster',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_tif_rgb_nodata'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_tif_rgb_nodata.tif', ]},
        ],
        TEST_DATA: {
            'bbox': (1679391.080, 6562360.440, 1679416.230, 6562381.790),
            'file_extensions': ['.tif'],
            'normalized_color_interp': ['Red', 'Green', 'Blue', 'Alpha'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_tif_rgb_nodata.png',
            'file_type': 'raster',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_tif_rgba'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_tif_rgba.tif', ]},
        ],
        TEST_DATA: {
            'bbox': (1679391.075, 6562360.437, 1679416.269, 6562381.831),
            'file_extensions': ['.tif'],
            'normalized_color_interp': ['Red', 'Green', 'Blue', 'Alpha'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_tif_rgba.png',
            'file_type': 'raster',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_tiff'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_tiff_rgba_opaque.tiff', ]},
        ],
        TEST_DATA: {
            'bbox': (1669480, 6580973, 1675352, 6586999,),
            'file_extensions': ['.tiff'],
            'normalized_color_interp': ['Red', 'Green', 'Blue'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_tiff.png',
            'file_type': 'raster',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_tif_tfw'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_tif_tfw_rgba_opaque.tif',
                            'sample/layman.layer/sample_tif_tfw_rgba_opaque.tfw']},
        ],
        TEST_DATA: {
            'bbox': (1669480, 6580973, 1675352, 6586999,),
            'file_extensions': ['.tif', '.tfw'],
            'normalized_color_interp': ['Red', 'Green', 'Blue'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_tiff.png',
            'file_type': 'raster',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_tif_colortable_nodata_opaque'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_tif_colortable_nodata_opaque.tif']},
        ],
        TEST_DATA: {
            'bbox': (868376, 522128, 940583, 593255),
            'file_extensions': ['.tif'],
            'normalized_color_interp': ['Palette'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_tif_colortable_nodata_opaque.png',
            'file_type': 'raster',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_tif_colortable_nodata'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_tif_colortable_nodata.tif']},
        ],
        TEST_DATA: {
            'bbox': (868376, 522128, 940583, 593255),
            'file_extensions': ['.tif'],
            'normalized_color_interp': ['Palette'],
            # 'thumbnail': '',
            'file_type': 'raster',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_tif_grayscale_alpha_nodata'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_tif_grayscale_alpha_nodata.tif']},
        ],
        TEST_DATA: {
            'bbox': (1823049.056, 6310009.44, 1826918.349, 6312703.749),
            'file_extensions': ['.tif'],
            'normalized_color_interp': ['Gray', 'Alpha'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_tif_grayscale_alpha_nodata.png',
            'file_type': 'raster',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_tif_grayscale_nodata_opaque'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif']},
        ],
        TEST_DATA: {
            'bbox': (1823060, 6310012, 1826914, 6312691),
            'file_extensions': ['.tif'],
            'normalized_color_interp': ['Gray'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_tif_grayscale_nodata_opaque.png',
            'file_type': 'raster',
        },
    },
}

LIST_ALL_PUBLICATIONS = list(PUBLICATIONS.keys())
LIST_LAYERS = [(workspace, publ_type, publication) for (workspace, publ_type, publication) in PUBLICATIONS
               if publ_type == LAYER_TYPE]
LIST_RASTER_LAYERS = [(workspace, publ_type, publication) for (workspace, publ_type, publication), values in PUBLICATIONS.items()
                      if publ_type == LAYER_TYPE and values[TEST_DATA].get('file_type') == 'raster']
LIST_VECTOR_LAYERS = [(workspace, publ_type, publication) for (workspace, publ_type, publication), values in PUBLICATIONS.items()
                      if publ_type == LAYER_TYPE and values[TEST_DATA].get('file_type') == 'vector']
