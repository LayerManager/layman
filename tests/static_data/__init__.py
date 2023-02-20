from collections import defaultdict
from layman import settings
from test_tools import process_client

COMMON_WORKSPACE = 'test_workspace'
WORKSPACE1 = 'test_workspace_1'
WORKSPACE2 = 'test_workspace_2'

LAYER_TYPE = process_client.LAYER_TYPE
MAP_TYPE = process_client.MAP_TYPE
DEFINITION = 'definition'
TEST_DATA = 'test_data'

OWNER = 'test_owner'
OWNER2 = 'test_owner2'
NOT_OWNER = 'test_not_owner'

USERS = {OWNER, OWNER2, NOT_OWNER, }
HEADERS = {user: process_client.get_authz_headers(user) for user in USERS}

MICKA_XML_LAYER_DIFF_LINES = [
    {'plus_line': '+    <gco:CharacterString>m-81c0debe-b2ea-4829-9b16-581083b29907</gco:CharacterString>\n',
     'minus_line_starts_with': '-    <gco:CharacterString>m',
     'minus_line_ends_with': '</gco:CharacterString>\n',
     },
    {'plus_line': '+    <gco:Date>2007-05-25</gco:Date>\n',
     'minus_line_starts_with': '-    <gco:Date>',
     'minus_line_ends_with': '</gco:Date>\n',
     },
    {'plus_line': '+                <gco:Date>2019-12-07</gco:Date>\n',
     'minus_line_starts_with': '-                <gco:Date>',
     'minus_line_ends_with': '</gco:Date>\n',
     },
]

PUBLICATIONS = {
    ################################################################################
    #                                    LAYERS
    ################################################################################
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_common_sld'): {
        DEFINITION: [
            {},
        ],
        TEST_DATA: {
            'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
        },
    },
    (OWNER, LAYER_TYPE, 'post_private_sld'): {
        DEFINITION: [
            {'headers': HEADERS[OWNER],
             'file_paths': ['sample/layman.layer/small_layer_with_id.geojson'],
             },
        ],
        TEST_DATA: {
            'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
            'users_can_read': [OWNER],
            'users_can_write': [OWNER],
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_strange_attributes_qml'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/strange_attribute_names.geojson'],
             'style_file': 'sample/style/strange_attribute_names.qml',
             },
        ],
        TEST_DATA: {
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'qml',
            'attributes': {'atraktivita geoturizmu', 'info', 'x,', 'y,', 'z,', 'ČÍslo'},
        },
    },
    (OWNER2, LAYER_TYPE, 'post_private_sld2'): {
        DEFINITION: [
            {'headers': HEADERS[OWNER2]},
        ],
        TEST_DATA: {
            'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
            'users_can_read': [OWNER2],
            'users_can_write': [OWNER2],
        },
    },
    (OWNER, LAYER_TYPE, 'post_private_write_sld'): {
        DEFINITION: [
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': 'EVERYONE', 'write': OWNER},
             },
        ],
        TEST_DATA: {
            'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
            'users_can_write': [OWNER],
        },
    },
    (OWNER, LAYER_TYPE, 'post_public_sld'): {
        DEFINITION: [
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': 'EVERYONE', 'write': 'EVERYONE'},
             },
        ],
        TEST_DATA: {
            'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'patch_3355bbox_sld'): {
        DEFINITION: [
            {},
            {'file_paths': ['test_tools/data/bbox/layer_3_3-5_5.geojson', ]},
        ],
        TEST_DATA: {
            'bbox': (3000, 3000, 5000, 5000),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
            'style_file_type': 'sld',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_common_qml'): {
        DEFINITION: [
            {'style_file': 'sample/style/small_layer.qml'},
        ],
        TEST_DATA: {
            'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'qml',
            'style_file_type': 'qml',
            'min_scale': '100000000',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_countries_qml'): {
        DEFINITION: [
            {'file_paths': ['/code/tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson'],
             'style_file': 'sample/style/ne_10m_admin_0_countries.qml'},
            {'title': 'Title defined'},
        ],
        TEST_DATA: {
            'title': 'Title defined',
            'thumbnail': 'sample/style/test_qgis_style_applied_in_thumbnail_layer.png',
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'qml',
            'style_file_type': 'qml',
            'min_scale': '200000000',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'patch_style_countries_qml'): {
        DEFINITION: [
            {'file_paths': ['/code/tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson']},
            {'style_file': 'sample/style/ne_10m_admin_0_countries.qml'},
            {'title': 'Title defined'}
        ],
        TEST_DATA: {
            'title': 'Title defined',
            'thumbnail': 'sample/style/test_qgis_style_applied_in_thumbnail_layer.png',
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'qml',
            'style_file_type': 'qml',
            'min_scale': '200000000',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'patch_style_110countries_sld'): {
        DEFINITION: [
            {'file_paths': ['/code/tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson']},
            {'style_file': 'sample/style/ne_10m_admin_0_countries.qml'},
            {'file_paths': ['/code/tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson']},
            {'style_file': 'sample/style/generic-blue_sld.xml'},
        ],
        TEST_DATA: {
            'thumbnail': 'sample/style/test_sld_style_applied_in_thumbnail_layer.png',
            'get_map': ('SRS=EPSG:3857&WIDTH=768&HEIGHT=752&BBOX=-30022616.05686392,-30569903.32873383,30022616.05686392,28224386.44929134',
                        'test_tools/data/thumbnail/countries_wms_blue.png',
                        2000,
                        ),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
            'style_file_type': 'sld',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_10countries_sld'): {
        DEFINITION: [
            {'file_paths': ['/code/tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson']},
        ],
        TEST_DATA: {
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_jp2'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_jp2_rgb.jp2', ],
             'headers': HEADERS[OWNER],
             'access_rights': {'read': OWNER, 'write': OWNER},
             },
        ],
        TEST_DATA: {
            'bbox': (1829708, 6308828.600, 1833166.200, 6310848.600),
            'file_extensions': ['.jp2'],
            'normalized_color_interp': ['Red', 'Green', 'Blue'],
            'normalized_overviews': 0,
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_jp2.png',
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
            'users_can_read': [OWNER],
            'users_can_write': [OWNER],
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
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_jp2_j2w'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_jp2_j2w_rgb.jp2',
                            'sample/layman.layer/sample_jp2_j2w_rgb.j2w', ], 'crs': 'EPSG:3857'},
        ],
        TEST_DATA: {
            'bbox': (1829708, 6308828.600, 1833166.200, 6310848.600),
            'file_extensions': ['.jp2', '.j2w'],
            'normalized_color_interp': ['Red', 'Green', 'Blue'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_jp2_j2w.png',
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
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
            'normalized_overviews': 2,
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_tif.png',
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
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
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
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
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_tif_rgba_4326'): {
        DEFINITION: [
            {},
            {'file_paths': ['sample/layman.layer/sample_tif_rgba_4326.tif', ]},
        ],
        TEST_DATA: {
            'bbox': (1679391.075, 6562360.443, 1679416.256, 6562381.831),
            'file_extensions': ['.tif'],
            'normalized_color_interp': ['Red', 'Green', 'Blue', 'Alpha'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_tif_rgba_4326.png',
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
            'micka_xml': {'filled_template': 'test_tools/data/micka/rest_test_filled_raster_template.xml',
                          'diff_lines': MICKA_XML_LAYER_DIFF_LINES,
                          'diff_lines_len': 29,
                          },
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
            'normalized_overviews': 1,
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_tiff.png',
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
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
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
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
            'normalized_overviews': 2,
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_tif_colortable_nodata_opaque.png',
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_tif_colortable_nodata_opaque_4326'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_tif_colortable_nodata_opaque_4326.tif']},
        ],
        TEST_DATA: {
            'bbox': (868375.99, 522100.63, 940557.77, 593254.99),
            'file_extensions': ['.tif'],
            'normalized_color_interp': ['Palette'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_tif_colortable_nodata_opaque_4326.png',
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
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
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_tif_colortable_nodata.png',
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_tif_grayscale_alpha_nodata'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_tif_grayscale_alpha_nodata.tif'],
             'style_file': 'sample/style/sample_tif_grayscale_alpha_nodata.sld'},
        ],
        TEST_DATA: {
            'bbox': (1823049.056, 6310009.44, 1826918.349, 6312703.749),
            'file_extensions': ['.tif'],
            'normalized_color_interp': ['Gray'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_tif_grayscale_alpha_nodata_styled.png',
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_tif_grayscale_alpha_nodata_4326'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_tif_grayscale_alpha_nodata_4326.tif']},
        ],
        TEST_DATA: {
            'bbox': (1823049.05, 6310001.12, 1826924.71, 6312703.74),
            'file_extensions': ['.tif'],
            'normalized_color_interp': ['Gray', 'Alpha'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_tif_grayscale_alpha_nodata_4326.png',
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
        },
    },
    (OWNER, LAYER_TYPE, 'post_tif_grayscale_nodata_opaque'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_tif_grayscale_nodata_opaque.tif'],
             'headers': HEADERS[OWNER],
             'title': 'None title',
             },
            {'title': 'Some title',
             'headers': HEADERS[OWNER],
             },
            {'access_rights': {'read': 'EVERYONE', 'write': 'EVERYONE'},
             'headers': HEADERS[OWNER],
             }
        ],
        TEST_DATA: {
            'bbox': (1823060, 6310012, 1826914, 6312691),
            'file_extensions': ['.tif'],
            'normalized_color_interp': ['Gray'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_tif_grayscale_nodata_opaque.png',
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
            'title': 'Some title',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_png_aux_rgba'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_png_aux_rgba.png',
                            'sample/layman.layer/sample_png_aux_rgba.png.aux.xml', ]},
        ],
        TEST_DATA: {
            'bbox': (2707260.9569237595, 7740717.799460372, 2708414.90486888, 7741573.954387397),
            'file_extensions': ['.png', '.png.aux.xml'],
            'normalized_color_interp': ['Red', 'Green', 'Blue', 'Alpha'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_png_rgba.png',
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_png_pgw_rgba'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_png_pgw_rgba.pgw',
                            'sample/layman.layer/sample_png_pgw_rgba.png', ], 'crs': 'EPSG:3857'},
        ],
        TEST_DATA: {
            'bbox': (2707260.9569237595424056, 7740717.7994603710249066, 2708414.9048688816837966, 7741573.9543873965740204),
            'file_extensions': ['.png', '.pgw'],
            'normalized_color_interp': ['Red', 'Green', 'Blue', 'Alpha'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_png_rgba.png',
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_png_aux_rgba_opaque'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_png_aux_rgba_opaque.png',
                            'sample/layman.layer/sample_png_aux_rgba_opaque.png.aux.xml', ]},
        ],
        TEST_DATA: {
            'bbox': (1731751.7587133494671434, 6535237.5194635167717934, 1741920.6898681195452809, 6544154.1191952852532268),
            'file_extensions': ['.png', '.png.aux.xml'],
            'normalized_color_interp': ['Red', 'Green', 'Blue'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_png_rgba_opaque.png',
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_jpg_aux_rgb'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_jpg_aux_rgb.jpg',
                            'sample/layman.layer/sample_jpg_aux_rgb.jpg.aux.xml', ]},
        ],
        TEST_DATA: {
            'bbox': (1679391.0800000000745058, 6562360.4400000004097819, 1679416.2299999999813735, 6562381.7900000000372529),
            'file_extensions': ['.jpg', '.jpg.aux.xml'],
            'normalized_color_interp': ['Red', 'Green', 'Blue'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_jpg_rgb.png',
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_jpg_jgw_rgb'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_jpg_jgw_rgb.jpg',
                            'sample/layman.layer/sample_jpg_jgw_rgb.jgw', ], 'crs': 'EPSG:3857'},
        ],
        TEST_DATA: {
            'bbox': (1679391.0800000000745058, 6562360.4400000004097819, 1679416.2299999999813735, 6562381.7900000000372529),
            'file_extensions': ['.jpg', '.jgw'],
            'normalized_color_interp': ['Red', 'Green', 'Blue'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_jpg_rgb.png',
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_jepg_jgw_rgb'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_jpeg_jgw_rgb.jpeg',
                            'sample/layman.layer/sample_jpeg_jgw_rgb.jgw', ], 'crs': 'EPSG:3857'},
        ],
        TEST_DATA: {
            'bbox': (1679391.0800000000745058, 6562360.4400000004097819, 1679416.2299999999813735, 6562381.7900000000372529),
            'file_extensions': ['.jpeg', '.jgw'],
            'normalized_color_interp': ['Red', 'Green', 'Blue'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_jpg_rgb.png',
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_jpg_aux_rgba'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_jpg_aux_rgba.jpg',
                            'sample/layman.layer/sample_jpg_aux_rgba.jpg.aux.xml', ]},
        ],
        TEST_DATA: {
            'bbox': (2707260.9569237595424056, 7740717.7994603719562292, 2708414.9048688798211515, 7741573.9543873965740204),
            'file_extensions': ['.jpg', '.jpg.aux.xml'],
            'normalized_color_interp': ['Red', 'Green', 'Blue', 'Alpha'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_jpg_rgba.png',
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_blue_style'): {
        DEFINITION: [
            {'file_paths': ['/code/tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson'],
             'style_file': 'sample/style/generic-blue_sld.xml'},
        ],
        TEST_DATA: {
            'thumbnail': 'sample/style/test_sld_style_applied_in_thumbnail_layer.png',
            'get_map': ('SRS=EPSG:3857&WIDTH=768&HEIGHT=752&BBOX=-30022616.05686392,-30569903.32873383,30022616.05686392,28224386.44929134',
                        'test_tools/data/thumbnail/countries_wms_blue.png',
                        2000,
                        ),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
            'style_file_type': 'sld',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_chunks_geojson_sld'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/small_layer.geojson'],
             'with_chunks': True,
             },
        ],
        TEST_DATA: {
            'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
        },
    },
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_chunks_tif_sld'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_tif_rgb.tif'],
             'with_chunks': True,
             },
        ],
        TEST_DATA: {
            'bbox': (1679391.080, 6562360.440, 1679416.230, 6562381.790),
            'file_extensions': ['.tif'],
            'normalized_color_interp': ['Red', 'Green', 'Blue'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_tif.png',
            'geodata_type': settings.GEODATA_TYPE_RASTER,
            'style_type': 'sld',
        },
    },
    (WORKSPACE1, LAYER_TYPE, 'test_publications_same_name_publ'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_tif_rgba_4326.tif', ]},
            {'file_paths': [
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.cpg',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.dbf',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.prj',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.README.html',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.shp',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.shx',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.VERSION.txt',
            ]},
        ],
        TEST_DATA: {
            'bbox': (-20026376.39, -20048966.1, 20026376.39, 18440002.895114247),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
            'micka_xml': {'filled_template': 'test_tools/data/micka/rest_test_filled_template.xml',
                          'diff_lines': MICKA_XML_LAYER_DIFF_LINES,
                          'diff_lines_len': 29,
                          },
        },
    },
    (WORKSPACE2, LAYER_TYPE, 'test_publications_same_name_publ'): {
        DEFINITION: [
            {},
        ],
        TEST_DATA: {
            'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
        },
    },
    (OWNER, LAYER_TYPE, 'patch_common_public_sld'): {
        DEFINITION: [
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': 'EVERYONE', 'write': 'EVERYONE'}, },
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': 'EVERYONE', 'write': 'EVERYONE'}, },
        ],
        TEST_DATA: {
            'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
        },
    },
    (OWNER, LAYER_TYPE, 'patch_common_public_sld2'): {
        DEFINITION: [
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': 'EVERYONE', 'write': 'EVERYONE'}, },
            {'headers': HEADERS[OWNER],
             },
        ],
        TEST_DATA: {
            'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
        },
    },
    (OWNER, LAYER_TYPE, 'patch_common_public_sld3'): {
        DEFINITION: [
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': OWNER, 'write': OWNER}, },
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': 'EVERYONE', 'write': 'EVERYONE'}, },
        ],
        TEST_DATA: {
            'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
        },
    },
    (OWNER, LAYER_TYPE, 'patch_private_sld'): {
        DEFINITION: [
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': OWNER, 'write': OWNER},
             },
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': OWNER, 'write': OWNER},
             },
        ],
        TEST_DATA: {
            'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
            'users_can_read': [OWNER],
            'users_can_write': [OWNER],
        },
    },
    (OWNER, LAYER_TYPE, 'patch_private_sld2'): {
        DEFINITION: [
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': OWNER, 'write': OWNER},
             },
            {'headers': HEADERS[OWNER],
             },
        ],
        TEST_DATA: {
            'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
            'users_can_read': [OWNER],
            'users_can_write': [OWNER],
        },
    },
    (OWNER, LAYER_TYPE, 'patch_private_sld3'): {
        DEFINITION: [
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': OWNER, 'write': OWNER},
             },
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': 'EVERYONE', },
             },
        ],
        TEST_DATA: {
            'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
            'users_can_write': [OWNER],
        },
    },
    (OWNER, LAYER_TYPE, 'patch_private_sld4'): {
        DEFINITION: [
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': 'EVERYONE', 'write': 'EVERYONE'},
             },
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': OWNER, 'write': OWNER},
             },
        ],
        TEST_DATA: {
            'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
            'users_can_read': [OWNER],
            'users_can_write': [OWNER],
        },
    },
    (OWNER, LAYER_TYPE, 'patch_private_sld5'): {
        DEFINITION: [
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': 'EVERYONE', 'write': 'EVERYONE'},
             },
            {'headers': HEADERS[OWNER],
             'access_rights': {'write': OWNER},
             },
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': OWNER},
             },
        ],
        TEST_DATA: {
            'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
            'users_can_read': [OWNER],
            'users_can_write': [OWNER],
        },
    },
    (OWNER, LAYER_TYPE, 'patch_private_sld6'): {
        DEFINITION: [
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': 'EVERYONE', 'write': 'EVERYONE'},
             },
            {'headers': HEADERS[OWNER],
             'access_rights': {'write': OWNER},
             },
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': f'{OWNER}, {OWNER2}'},
             },
        ],
        TEST_DATA: {
            'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
            'users_can_read': [OWNER, OWNER2],
            'users_can_write': [OWNER],
        },
    },
    (OWNER, LAYER_TYPE, 'patch_common_public_sld4'): {
        DEFINITION: [
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': 'EVERYONE', 'write': 'EVERYONE'},
             },
            {'headers': HEADERS[OWNER],
             'access_rights': {'write': OWNER},
             },
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': f'{OWNER}, {OWNER2}, EVERYONE'},
             },
            {'headers': HEADERS[OWNER],
             'access_rights': {'read': 'EVERYONE', 'write': 'EVERYONE'},
             },
        ],
        TEST_DATA: {
            'bbox': (1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699),
            'geodata_type': settings.GEODATA_TYPE_VECTOR,
            'style_type': 'sld',
        },
    },
    ################################################################################
    #                                     MAPS
    ################################################################################
    (COMMON_WORKSPACE, MAP_TYPE, 'post_common'): {
        DEFINITION: [
            {},
        ],
        TEST_DATA: {
            'bbox': (1627490.9553976597, 6547334.172794042, 1716546.5480322787, 6589515.35758913),
        },
    },
    (COMMON_WORKSPACE, MAP_TYPE, 'post_internal_layer'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.map/internal_url_thumbnail.json', ]},
        ],
        TEST_DATA: {
            'layers': [(COMMON_WORKSPACE, LAYER_TYPE, 'post_blue_style'), ],
            'operates_on': {(COMMON_WORKSPACE, LAYER_TYPE, 'post_blue_style'), },
            'thumbnail': 'sample/style/test_sld_style_applied_in_map_thumbnail_map.png',
        },
    },
    (OWNER, MAP_TYPE, 'post_private'): {
        DEFINITION: [
            {'headers': HEADERS[OWNER]},
        ],
        TEST_DATA: {
            'bbox': (1627490.9553976597, 6547334.172794042, 1716546.5480322787, 6589515.35758913),
            'users_can_read': [OWNER],
            'users_can_write': [OWNER],
        },
    },
    (COMMON_WORKSPACE, MAP_TYPE, 'patch_3355bbox'): {
        DEFINITION: [
            {},
            {'file_paths': ['test_tools/data/bbox/map_3_3-5_5.json', ]},
        ],
        TEST_DATA: {
            'title': 'Administrativní členění Libereckého kraje',
            'bbox': (3000, 3000, 5000, 5000),
        },
    },
    (OWNER, MAP_TYPE, 'post_unauthorized_layer'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.map/internal_url_unauthorized_layer.json'],
             'access_rights': {'read': 'EVERYONE',
                               'write': f"{OWNER},{OWNER2}",
                               },
             'headers': HEADERS[OWNER],
             },
        ],
        TEST_DATA: {
            'layers': [(OWNER, LAYER_TYPE, 'post_private_sld'), (OWNER2, LAYER_TYPE, 'post_private_sld2'), ],
            'operates_on': {(OWNER, LAYER_TYPE, 'post_private_sld'), },
            'users_can_write': [OWNER, OWNER2],
        },
    },
    (OWNER, MAP_TYPE, 'patch_unauthorized_layer'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.map/internal_url_unauthorized_layer.json'],
             'access_rights': {'read': 'EVERYONE',
                               'write': f"{OWNER},{OWNER2}",
                               },
             'headers': HEADERS[OWNER],
             },
            {'headers': HEADERS[OWNER2], }
        ],
        TEST_DATA: {
            'layers': [(OWNER, LAYER_TYPE, 'post_private_sld'), (OWNER2, LAYER_TYPE, 'post_private_sld2'), ],
            'operates_on': {(OWNER2, LAYER_TYPE, 'post_private_sld2'), },
            'users_can_write': [OWNER, OWNER2],
        },
    },
    (WORKSPACE1, MAP_TYPE, 'test_publications_same_name_publ'): {
        DEFINITION: [
            {},
        ],
        TEST_DATA: {
            'bbox': (1627490.9553976597, 6547334.172794042, 1716546.5480322787, 6589515.35758913),
        },
    },
    (WORKSPACE2, MAP_TYPE, 'test_publications_same_name_publ'): {
        DEFINITION: [
            {},
        ],
        TEST_DATA: {
            'bbox': (1627490.9553976597, 6547334.172794042, 1716546.5480322787, 6589515.35758913),
        },
    },
}

# PUBLICATIONS = {(ws, pt, pn): value for (ws, pt, pn), value in PUBLICATIONS.items()
#                 if (ws, pt, pn) in {(COMMON_WORKSPACE, LAYER_TYPE, 'post_common_sld'),
#                                     (COMMON_WORKSPACE, LAYER_TYPE, 'post_common_qml'),
#                                     (COMMON_WORKSPACE, LAYER_TYPE, 'post_jp2'),
#                                     (COMMON_WORKSPACE, MAP_TYPE, 'post_internal_layer'),
#                                     (COMMON_WORKSPACE, LAYER_TYPE, 'post_blue_style'),
#                                     (COMMON_WORKSPACE, LAYER_TYPE, 'post_10countries_sld'),
#                                     }}

LIST_ALL_PUBLICATIONS = list(PUBLICATIONS.keys())
LIST_LAYERS = [(workspace, publ_type, publication) for (workspace, publ_type, publication) in PUBLICATIONS
               if publ_type == LAYER_TYPE]
LIST_RASTER_LAYERS = [(workspace, publ_type, publication) for (workspace, publ_type, publication), values in PUBLICATIONS.items()
                      if publ_type == LAYER_TYPE and values[TEST_DATA].get('geodata_type') == settings.GEODATA_TYPE_RASTER]
LIST_VECTOR_LAYERS = [(workspace, publ_type, publication) for (workspace, publ_type, publication), values in PUBLICATIONS.items()
                      if publ_type == LAYER_TYPE and values[TEST_DATA].get('geodata_type') == settings.GEODATA_TYPE_VECTOR]
LIST_SLD_LAYERS = [(workspace, publ_type, publication) for (workspace, publ_type, publication), values in PUBLICATIONS.items()
                   if publ_type == LAYER_TYPE and values[TEST_DATA].get('style_type') == 'sld']
LIST_QML_LAYERS = [(workspace, publ_type, publication) for (workspace, publ_type, publication), values in PUBLICATIONS.items()
                   if publ_type == LAYER_TYPE and values[TEST_DATA].get('style_type') == 'qml']

LIST_INTERNAL_MAPS = [(workspace, publ_type, publication) for (workspace, publ_type, publication), values in PUBLICATIONS.items()
                      if publ_type == MAP_TYPE and values[TEST_DATA].get('layers')]

WORKSPACES = {workspace for workspace, _, _ in PUBLICATIONS}

assert len(WORKSPACES) > 0, WORKSPACES
assert len(USERS) > 0, USERS
assert len(HEADERS) > 0, HEADERS

assert len(LIST_ALL_PUBLICATIONS) > 0, LIST_ALL_PUBLICATIONS
assert len(LIST_LAYERS) > 0, LIST_LAYERS
assert len(LIST_RASTER_LAYERS) > 0, LIST_RASTER_LAYERS
assert len(LIST_VECTOR_LAYERS) > 0, LIST_VECTOR_LAYERS
assert len(LIST_SLD_LAYERS) > 0, LIST_SLD_LAYERS
assert len(LIST_QML_LAYERS) > 0, LIST_QML_LAYERS
assert len(LIST_INTERNAL_MAPS) > 0, LIST_INTERNAL_MAPS
assert any('normalized_overviews' in v[TEST_DATA] for v in PUBLICATIONS.values())


def assert_same_name_publications(publications):
    types_by_workspace_and_name = defaultdict(set)
    for workspace, publ_type, publ_name in publications:
        types_by_workspace_and_name[(workspace, publ_name)].add(publ_type)
    same_name_same_workspace = {k: v for k, v in types_by_workspace_and_name.items() if len(v) > 1}
    assert len(same_name_same_workspace) > 0

    workspaces_by_type_and_name = defaultdict(set)
    for workspace, publ_type, publ_name in publications:
        workspaces_by_type_and_name[(publ_type, publ_name)].add(workspace)
    same_name_same_type = {k: v for k, v in workspaces_by_type_and_name.items() if len(v) > 1}
    assert len(same_name_same_type) > 0


assert_same_name_publications(PUBLICATIONS)

assert all(set(test_data.get('users_can_read', set())).issubset(USERS) for test_data in PUBLICATIONS.values())
assert all(set(test_data.get('users_can_write', set())).issubset(USERS) for test_data in PUBLICATIONS.values())
