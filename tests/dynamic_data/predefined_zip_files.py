from test_tools import process_client

SMALL_LAYER_ZIP = {
    'file_paths': ['sample/layman.layer/small_layer.geojson'],
    'compress': True,
}

NE_110M_ADMIN_0_BOUNDARY_LINES_LAND = {
    'file_paths': [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.cpg',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.dbf',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.prj',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.README.html',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shx',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.VERSION.txt',
    ],
    'compress': True,
    'compress_settings': process_client.CompressTypeDef(archive_name='ne_110m_admin_0_boundary lines land +ěščřžýáí',
                                                        inner_directory='/ne_110m_admin_0_boundary lines land +ěščřžýáí/',
                                                        file_name_suffix=' ížě',
                                                        ),
}

SAMPLE_TIF_TFW_RGBA_OPAQUE = {
    'file_paths': [
        'sample/layman.layer/sample_tif_tfw_rgba_opaque.tfw',
        'sample/layman.layer/sample_tif_tfw_rgba_opaque.tif',
    ],
    'compress': True,
    'compress_settings': process_client.CompressTypeDef(archive_name=None,
                                                        inner_directory='/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque/',
                                                        file_name_suffix=None,
                                                        ),
}

SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE = {
    'file_paths': [
        'sample/layman.layer/sample_tif_colortable_nodata_opaque.tif',
        'sample/layman.layer/sample_tif_colortable_nodata_opaque.tif.aux.xml',
    ],
    'compress': True,
    'compress_settings': process_client.CompressTypeDef(archive_name=None,
                                                        inner_directory='/sample_tif_colortable_nodata_opaque/',
                                                        file_name_suffix=None,
                                                        ),
}
