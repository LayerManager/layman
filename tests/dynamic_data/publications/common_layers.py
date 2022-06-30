import tests.asserts.final.publication as publication
import tests.asserts.processing as processing
from test_tools import process_client
from ... import PublicationValues, dynamic_data as consts, Action

SMALL_LAYER = PublicationValues(
    type=process_client.LAYER_TYPE,
    definition=dict(),
    info_values={
        'exp_publication_detail': {
            'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.335616991],
            'native_crs': 'EPSG:4326',
            'native_bounding_box': [14.114369, 48.964832, 14.126824, 48.970612],
        },
        'file_extension': 'geojson',
        'publ_type_detail': ('vector', 'sld'),
    },
    thumbnail='sample/style/basic_sld.png',
)

SMALL_LAYER_ZIP = PublicationValues(
    type=process_client.LAYER_TYPE,
    definition={
        'file_paths': ['sample/layman.layer/small_layer.geojson'],
        'compress': True,
    },
    info_values={
        **SMALL_LAYER.info_values,
        'file_extension': 'zip/small_layer.geojson',
        'gdal_prefix': '/vsizip/',
    },
    thumbnail=SMALL_LAYER.thumbnail,
)

SMALL_LAYER_QML = PublicationValues(
    type=process_client.LAYER_TYPE,
    definition={
        'style_file': 'sample/style/small_layer.qml'
    },
    info_values={
        **SMALL_LAYER.info_values,
        'publ_type_detail': ('vector', 'qml'),
    },
    thumbnail='sample/style/small_layer_qml.png',
)

NE_110M_ADMIN_0_BOUNDARY_LINES_LAND = PublicationValues(
    type=process_client.LAYER_TYPE,
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
            'bounding_box': [-15695801.072582014, -7341864.739114419, 15699816.562538767, 11122367.192100525],
            'native_crs': 'EPSG:4326',
            'native_bounding_box': [-140.99778, -54.89681, 141.03385176001382, 70.16419],
        },
        'file_extension': 'shp',
        'publ_type_detail': ('vector', 'sld'),
    },
    thumbnail='test_tools/data/thumbnail/ne_110m_admin_0_boundary_lines_land.png',
)

NE_110M_ADMIN_0_BOUNDARY_LINES_LAND_ZIP = PublicationValues(
    type=process_client.LAYER_TYPE,
    definition={
        **NE_110M_ADMIN_0_BOUNDARY_LINES_LAND.definition,
        'compress': True,
        'compress_settings': process_client.CompressTypeDef(archive_name='ne_110m_admin_0_boundary lines land +ěščřžýáí',
                                                            inner_directory='/ne_110m_admin_0_boundary lines land +ěščřžýáí/',
                                                            file_name='ne_110m_admin_0_boundary_lines_land ížě',
                                                            ),
    },
    info_values={
        **NE_110M_ADMIN_0_BOUNDARY_LINES_LAND.info_values,
        'file_extension': 'zip/ne_110m_admin_0_boundary lines land +ěščřžýáí/ne_110m_admin_0_boundary_lines_land ížě.shp',
        'gdal_prefix': '/vsizip/',
    },
    thumbnail=NE_110M_ADMIN_0_BOUNDARY_LINES_LAND.thumbnail,
)

SAMPLE_TIF_TFW_RGBA_OPAQUE = PublicationValues(
    type=process_client.LAYER_TYPE,
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
            'native_bounding_box': [1669480.0, 6580973.000000007, 1675351.9999999802, 6586999.0],
        },
        'file_extension': 'tif',
        'publ_type_detail': ('raster', 'sld'),
    },
    thumbnail='test_tools/data/thumbnail/raster_layer_tiff.png',
)

SAMPLE_TIF_TFW_RGBA_OPAQUE_ZIP = PublicationValues(
    type=process_client.LAYER_TYPE,
    definition={
        **SAMPLE_TIF_TFW_RGBA_OPAQUE.definition,
        'compress': True,
        'compress_settings': process_client.CompressTypeDef(
            inner_directory='/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque/',
        ),
    },
    info_values={
        **SAMPLE_TIF_TFW_RGBA_OPAQUE.info_values,
        'file_extension': 'zip/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque/sample_tif_tfw_rgba_opaque.tif',
        'gdal_prefix': '/vsizip/',
    },
    thumbnail=SAMPLE_TIF_TFW_RGBA_OPAQUE.thumbnail,
)

SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE = PublicationValues(
    type=process_client.LAYER_TYPE,
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
            'native_bounding_box': [868376.0, 522128.0, 940583.0, 593255.0],
        },
        'publ_type_detail': ('raster', 'sld'),
    },
    thumbnail='test_tools/data/thumbnail/raster_layer_tif_colortable_nodata_opaque.png',
)

SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE_ZIP = PublicationValues(
    type=process_client.LAYER_TYPE,
    definition={
        **SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE.definition,
        'compress': True,
        'compress_settings': process_client.CompressTypeDef(inner_directory='/sample_tif_colortable_nodata_opaque/', ),
    },
    info_values={
        **SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE.info_values,
        'file_extension': 'zip/sample_tif_colortable_nodata_opaque/sample_tif_colortable_nodata_opaque.tif',
        'gdal_prefix': '/vsizip/',
    },
    thumbnail=SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE.thumbnail,
)

DEFAULT_POST = {
    consts.KEY_ACTION: {
        consts.KEY_CALL: Action(process_client.publish_workspace_publication,
                                dict()),
        consts.KEY_RESPONSE_ASSERTS: [
            Action(processing.response.valid_post, dict()),
        ],
    },
    consts.KEY_FINAL_ASSERTS: [
        *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
    ]
}

DEFAULT_POST_DICT = {
    process_client.LAYER_TYPE: DEFAULT_POST,
    process_client.MAP_TYPE: {
        consts.KEY_ACTION: {
            consts.KEY_CALL: Action(process_client.publish_workspace_publication,
                                    dict()),
            consts.KEY_RESPONSE_ASSERTS: [
                Action(processing.response.valid_post, dict()),
            ],
        },
        consts.KEY_FINAL_ASSERTS: [
            *publication.IS_MAP_COMPLETE_AND_CONSISTENT,
        ]
    },
}

DEFAULT_ACTIONS = [
    ('post', process_client.publish_workspace_publication, []),
    ('patch', process_client.patch_workspace_publication, [DEFAULT_POST])
]

LAYER_VECTOR_SLD = SMALL_LAYER
LAYER_VECTOR_QML = SMALL_LAYER_QML
LAYER_RASTER = SAMPLE_TIF_TFW_RGBA_OPAQUE
