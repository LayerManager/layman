from db import TableUri
from layman import settings
from test_tools import process_client, external_db
from ... import TestPublicationValues

SMALL_LAYER = TestPublicationValues(
    type=process_client.LAYER_TYPE,
    definition={
        'file_paths': ['sample/layman.layer/small_layer.geojson'],
    },
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
    legend_image='tests/dynamic_data/publications/layer_by_used_servers/legend_vector_sld.png',
)

SMALL_LAYER_ZIP = TestPublicationValues(
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

SMALL_LAYER_QML = TestPublicationValues(
    type=process_client.LAYER_TYPE,
    definition={
        'file_paths': ['sample/layman.layer/small_layer.geojson'],
        'style_file': 'sample/style/small_layer.qml',
    },
    info_values={
        **SMALL_LAYER.info_values,
        'publ_type_detail': ('vector', 'qml'),
    },
    thumbnail='sample/style/small_layer_qml.png',
    legend_image=None,  # because layer name appears in the image
)

NE_110M_ADMIN_0_BOUNDARY_LINES_LAND = TestPublicationValues(
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

SAMPLE_TIF_TFW_RGBA_OPAQUE = TestPublicationValues(
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
    legend_image='tests/dynamic_data/publications/layer_by_used_servers/legend_raster.png',
)

SAMPLE_TIF_COLORTABLE_NODATA_OPAQUE = TestPublicationValues(
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

EMPTY_MAP = TestPublicationValues(
    type=process_client.MAP_TYPE,
    definition={},
    info_values={
        'exp_publication_detail': {
            'bounding_box': [1627490.9553976597, 6547334.172794042, 1716546.5480322787, 6589515.35758913],
            'native_crs': 'EPSG:3857',
            'native_bounding_box': [1627490.9553976597, 6547334.172794042, 1716546.5480322787, 6589515.35758913],
            'description': 'Na tematické mapě při přiblížení jsou postupně zobrazované administrativní celky Libereckého kraje : okresy, OPÚ, ORP a obce.'
        },
    },
    thumbnail=None,
)

INPUT_FILE_PATH = 'sample/layman.layer/small_layer.geojson'
EXTERNAL_DB_TABLE = '_small_LAYER_by_used_servers'
EXTERNAL_DB_SCHEMA = 'public'

LAYER_EXTERNAL_TABLE_SLD = TestPublicationValues(
    type=process_client.LAYER_TYPE,
    definition={
        'external_table_uri': f"{external_db.URI_STR}?schema={EXTERNAL_DB_SCHEMA}&table={EXTERNAL_DB_TABLE}&geo_column=wkb_geometry",
    },
    info_values={
        'publ_type_detail': (settings.GEODATA_TYPE_VECTOR, 'sld'),
        'exp_publication_detail': {
            'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.335616991],
            'native_crs': 'EPSG:4326',
            'native_bounding_box': [14.114369, 48.964832, 14.126824, 48.970612],
        },
        'external_table_uri': TableUri(
            db_uri_str=external_db.URI_STR,
            schema=EXTERNAL_DB_SCHEMA,
            table=EXTERNAL_DB_TABLE,
            geo_column='wkb_geometry',
            primary_key_column=settings.OGR_DEFAULT_PRIMARY_KEY,
        ),
    },
    thumbnail=None,
    legend_image='tests/dynamic_data/publications/layer_by_used_servers/legend_vector_sld.png',
)

LAYER_EXTERNAL_TABLE_QML = TestPublicationValues(
    type=process_client.LAYER_TYPE,
    definition={
        'external_table_uri': f"{external_db.URI_STR}?schema={EXTERNAL_DB_SCHEMA}&table={EXTERNAL_DB_TABLE}&geo_column=wkb_geometry",
        'style_file': 'sample/style/small_layer.qml'
    },
    info_values={
        'publ_type_detail': (settings.GEODATA_TYPE_VECTOR, 'sld'),
        'exp_publication_detail': {
            'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.335616991],
            'native_crs': 'EPSG:4326',
            'native_bounding_box': [14.114369, 48.964832, 14.126824, 48.970612],
        },
        'external_table_uri': TableUri(
            db_uri_str=external_db.URI_STR,
            schema=EXTERNAL_DB_SCHEMA,
            table=EXTERNAL_DB_TABLE,
            geo_column='wkb_geometry',
            primary_key_column=settings.OGR_DEFAULT_PRIMARY_KEY,
        ),
    },
    thumbnail=None,
    legend_image=None,  # because layer name appears in the image
)

LAYER_VECTOR_SLD = SMALL_LAYER
LAYER_VECTOR_QML = SMALL_LAYER_QML
LAYER_RASTER = SAMPLE_TIF_TFW_RGBA_OPAQUE
MAP_EMPTY = EMPTY_MAP
