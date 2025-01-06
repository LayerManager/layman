from collections import namedtuple, OrderedDict

from layman import settings
from layman.util import url_for
from ..common.util import PUBLICATION_NAME_PATTERN, PUBLICATION_MAX_LENGTH

LAYER_TYPE = __name__

LAYERNAME_PATTERN = PUBLICATION_NAME_PATTERN
LAYERNAME_MAX_LENGTH = PUBLICATION_MAX_LENGTH
SAFE_PG_IDENTIFIER_PATTERN = r"^[a-zA-Z_][a-zA-Z_0-9]*$"
ATTRNAME_PATTERN = SAFE_PG_IDENTIFIER_PATTERN


def get_layer_type_def():
    return PUBLICATION_TYPES[LAYER_TYPE]


def get_layer_sources():
    return get_layer_type_def()['internal_sources']


def get_layer_info_keys(*, geodata_type, original_data_source):
    if geodata_type == settings.GEODATA_TYPE_VECTOR:
        key = (geodata_type, original_data_source)
    else:
        key = geodata_type
    result = get_layer_type_def()['info_keys'][key]
    return result


def get_layer_patch_keys():
    return get_layer_type_def()['patch_keys']


LAYER_REST_PATH_NAME = "layers"


from ..common import InternalSourceTypeDef
from .rest_workspace_layers import bp as workspace_layers_bp
from .rest_workspace_layer import bp as workspace_layer_bp
from .rest_workspace_layer_chunk import bp as workspace_layer_chunk_bp
from .rest_workspace_layer_thumbnail import bp as workspace_layer_thumbnail_bp
from .rest_workspace_layer_style import bp as workspace_layer_style_bp
from .rest_workspace_layer_metadata_comparison import bp as workspace_layer_metadata_comparison_bp
from .rest_layers import bp as layers_bp

PUBLICATION_TYPES = {
    f'{LAYER_TYPE}': {
        'type': LAYER_TYPE,  # unique type name, same as dict key
        'module': __name__,  # name of module that defines the type
        'rest_path_name': LAYER_REST_PATH_NAME,
        'workspace_blueprints': [  # blueprints to register
            workspace_layers_bp,
            workspace_layer_bp,
            workspace_layer_chunk_bp,
            workspace_layer_thumbnail_bp,
            workspace_layer_style_bp,
            workspace_layer_metadata_comparison_bp,
        ],
        'blueprints': [  # blueprints to register
            layers_bp,
        ],
        # see also .util.TASKS_TO_LAYER_INFO_KEYS
        'internal_sources': OrderedDict([  # internal sources to process when new source is published
            ('layman.layer.filesystem.uuid', InternalSourceTypeDef(info_items=[]),),
            ('layman.layer.prime_db_schema.table', InternalSourceTypeDef(info_items=[
                'access_rights', 'name', 'title', 'uuid', 'bounding_box', 'style_type', 'native_crs',
                'native_bounding_box', 'geodata_type', 'updated_at', 'id', 'type', 'image_mosaic', 'table_uri',
                'original_data_source', 'wfs_wms_status', 'layer_maps', 'description', ]),),
            ('layman.layer.filesystem.input_chunk', InternalSourceTypeDef(info_items=['file', ]),),
            ('layman.layer.filesystem.input_file', InternalSourceTypeDef(info_items=['file', ]),),
            ('layman.layer.filesystem.input_style', InternalSourceTypeDef(info_items=[]),),
            ('layman.layer.filesystem.gdal', InternalSourceTypeDef(info_items=['file', ]),),
            ('layman.layer.db.table', InternalSourceTypeDef(info_items=['db', ]),),
            ('layman.layer.prime_db_schema.file_data', InternalSourceTypeDef(info_items=[]),),
            ('layman.layer.qgis.wms', InternalSourceTypeDef(info_items=['style', 'wms', ]),),
            ('layman.layer.geoserver.wfs', InternalSourceTypeDef(info_items=['wfs', ]),),
            ('layman.layer.geoserver.wms', InternalSourceTypeDef(info_items=['wms', ]),),
            ('layman.layer.geoserver.sld', InternalSourceTypeDef(info_items=['style', ]),),
            ('layman.layer.prime_db_schema.wfs_wms_status', InternalSourceTypeDef(info_items=[]),),
            ('layman.layer.filesystem.thumbnail', InternalSourceTypeDef(info_items=['thumbnail', ]),),
            ('layman.layer.micka.soap', InternalSourceTypeDef(info_items=['metadata', ]),),
        ]),
        'task_modules': {
            'layman.layer.db.tasks',
            'layman.layer.prime_db_schema.tasks',
            'layman.layer.filesystem.tasks',
            'layman.layer.qgis.tasks',
            'layman.layer.geoserver.tasks',
            'layman.layer.micka.tasks',
        },
        'layman.common.filesystem': {
            'publications_dir': 'layers'
        },
        'layman.layer.qgis': {
            'publications_dir': 'layers'
        },
        'layman.common.metadata': {
            'syncable_properties': {
                'abstract',
                'extent',
                'graphic_url',
                'identifier',
                'layer_endpoint',
                'language',
                'revision_date',
                'reference_system',
                'spatial_resolution',
                'temporal_extent',
                'title',
                'wfs_url',
                'wms_url',
            }
        },
        'info_keys': {
            (settings.GEODATA_TYPE_VECTOR, settings.EnumOriginalDataSource.FILE.value): {
                'name', 'uuid', 'layman_metadata', 'url', 'title', 'description', 'updated_at', 'wms', 'wfs', 'thumbnail', 'file',
                'db', 'metadata', 'style', 'access_rights', 'bounding_box', 'native_crs', 'native_bounding_box',
                'original_data_source', 'geodata_type', 'db_table',
            },
            (settings.GEODATA_TYPE_VECTOR, settings.EnumOriginalDataSource.TABLE.value): {
                'name', 'uuid', 'layman_metadata', 'url', 'title', 'description', 'updated_at', 'wms', 'wfs', 'thumbnail',
                'db', 'metadata', 'style', 'access_rights', 'bounding_box', 'native_crs', 'native_bounding_box',
                'original_data_source', 'geodata_type',
            },
            settings.GEODATA_TYPE_RASTER: {
                'name', 'uuid', 'layman_metadata', 'url', 'title', 'description', 'updated_at', 'wms', 'thumbnail', 'file', 'metadata',
                'style', 'access_rights', 'bounding_box', 'native_crs', 'native_bounding_box', 'image_mosaic',
                'original_data_source', 'geodata_type',
            },
            settings.GEODATA_TYPE_UNKNOWN: {
                'name', 'uuid', 'layman_metadata', 'url', 'title', 'description', 'updated_at', 'wms', 'thumbnail', 'file', 'metadata',
                'style', 'access_rights', 'bounding_box', 'native_crs', 'native_bounding_box', 'original_data_source', 'geodata_type',
            },
        },
        'multi_info_keys_to_remove': [],
        'patch_keys': ['name', 'uuid', 'url', 'files_to_upload'],
    }
}

StyleTypeDef = namedtuple('StyleTypeDef', ['code',
                                           'root_element',
                                           'extension',
                                           'store_in_geoserver'
                                           ])
STYLE_TYPES_DEF = [StyleTypeDef('sld',
                                'StyledLayerDescriptor',
                                'sld',
                                True,
                                ),
                   StyleTypeDef('qml',
                                'qgis',
                                'qml',
                                False,
                                ),
                   ]
NO_STYLE_DEF = STYLE_TYPES_DEF[0]


def get_workspace_publication_url(workspace, publication_name, *, x_forwarded_items=None):
    return url_for('rest_workspace_layer.get', layername=publication_name, workspace=workspace, x_forwarded_items=x_forwarded_items)
