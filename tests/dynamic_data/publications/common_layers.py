from ... import PublicationValues

LAYERS = {
    'small_layer': PublicationValues(
        definition=dict(),
        info_values={
                    'exp_publication_detail': {
                        'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699],
                        'native_crs': 'EPSG:3857',
                        'native_bounding_box': [1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699, 'EPSG:3857'],
                    },
                    'file_extension': 'geojson',
                    'publ_type_detail': ('vector', 'sld'),
                },
        thumbnail='sample/style/basic_sld.png',
    ),
    'ne_110m_admin_0_boundary_lines_land': PublicationValues(
        definition={
            'file_paths': [
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.cpg',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.dbf',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.prj',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.README.html',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shx',
                'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.VERSION.txt',
            ],
        },
        info_values={
                    'exp_publication_detail': {
                        'bounding_box': [-15695801.072582014, -7341864.739114417, 15699816.562538767, 11122367.192100529],
                        'native_crs': 'EPSG:3857',
                        'native_bounding_box': [-15695801.072582014, -7341864.739114417, 15699816.562538767, 11122367.192100529, 'EPSG:3857'],
                    },
                    'file_extension': 'shp',
                    'publ_type_detail': ('vector', 'sld'),
                },
        thumbnail='test_tools/data/thumbnail/ne_110m_admin_0_boundary_lines_land.png',
    ),
    'sample_tif_tfw_rgba_opaque': PublicationValues(
        definition={
            'file_paths': [
                'sample/layman.layer/sample_tif_tfw_rgba_opaque.tfw',
                'sample/layman.layer/sample_tif_tfw_rgba_opaque.tif',
            ],
        },
        info_values={
            'exp_publication_detail': {
                'bounding_box': [1669480.0, 6580973.000000007, 1675351.9999999802, 6586999.0],
                'native_crs': 'EPSG:3857',
                'native_bounding_box': [1669480.0, 6580973.000000007, 1675351.9999999802, 6586999.0, 'EPSG:3857'],
            },
            'publ_type_detail': ('raster', 'sld'),
        },
        thumbnail='test_tools/data/thumbnail/raster_layer_tiff.png',
    ),
    'sample_tif_colortable_nodata_opaque': PublicationValues(
        definition={
            'file_paths': [
                'sample/layman.layer/sample_tif_colortable_nodata_opaque.tif',
                'sample/layman.layer/sample_tif_colortable_nodata_opaque.tif.aux.xml',
            ],
        },
        info_values={
            'exp_publication_detail': {
                'bounding_box': [868376.0, 522128.0, 940583.0, 593255.0],
                'native_crs': 'EPSG:3857',
                'native_bounding_box': [868376.0, 522128.0, 940583.0, 593255.0, 'EPSG:3857'],
            },
            'publ_type_detail': ('raster', 'sld'),
        },
        thumbnail='test_tools/data/thumbnail/raster_layer_tif_colortable_nodata_opaque.png',
    ),
}
