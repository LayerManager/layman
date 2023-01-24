from enum import Enum
from collections import namedtuple, OrderedDict
LAYER_TYPE = __name__


class EnumTableType(Enum):
    INTERNAL = 'internal'
    EXTERNAL = 'external'


def get_layer_type_def():
    return PUBLICATION_TYPES[LAYER_TYPE]


def get_layer_sources():
    return get_layer_type_def()['internal_sources']


def get_layer_info_keys(*, file_type, is_external_table):
    if file_type == settings.FILE_TYPE_VECTOR:
        table_type = EnumTableType.EXTERNAL if is_external_table else EnumTableType.INTERNAL
        key = (file_type, table_type)
    else:
        key = file_type
    result = get_layer_type_def()['info_keys'][key]
    return result


LAYER_REST_PATH_NAME = "layers"


from layman import settings
from layman.util import url_for
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
            ('layman.layer.prime_db_schema.table', InternalSourceTypeDef(info_items=['access_rights', 'name', 'title', 'uuid',
                                                                                     'bounding_box', 'style_type', 'native_crs',
                                                                                     'native_bounding_box', 'file_type', 'updated_at', 'id', 'type', 'image_mosaic',
                                                                                     'table_uri', 'is_external_table']),),
            ('layman.layer.filesystem.input_chunk', InternalSourceTypeDef(info_items=['file', ]),),
            ('layman.layer.filesystem.input_file', InternalSourceTypeDef(info_items=['file', ]),),
            ('layman.layer.filesystem.input_style', InternalSourceTypeDef(info_items=[]),),
            ('layman.layer.filesystem.gdal', InternalSourceTypeDef(info_items=['file', ]),),
            ('layman.layer.db.table', InternalSourceTypeDef(info_items=['db_table', ]),),
            ('layman.layer.prime_db_schema.file_data', InternalSourceTypeDef(info_items=[]),),
            ('layman.layer.qgis.wms', InternalSourceTypeDef(info_items=['style', 'wms', ]),),
            ('layman.layer.geoserver.wfs', InternalSourceTypeDef(info_items=['wfs', 'description', ]),),
            ('layman.layer.geoserver.wms', InternalSourceTypeDef(info_items=['wms', 'description', ]),),
            ('layman.layer.geoserver.sld', InternalSourceTypeDef(info_items=['style', ]),),
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
            (settings.FILE_TYPE_VECTOR, EnumTableType.INTERNAL): {'name', 'uuid', 'layman_metadata', 'url', 'title', 'description',
                                                                  'updated_at', 'wms', 'wfs', 'thumbnail', 'file', 'db_table',
                                                                  'metadata',
                                                                  'style', 'sld', 'access_rights', 'bounding_box', 'native_crs',
                                                                  'native_bounding_box', },
            (settings.FILE_TYPE_VECTOR, EnumTableType.EXTERNAL): {'name', 'uuid', 'layman_metadata', 'url', 'title', 'description',
                                                                  'updated_at', 'wms', 'wfs', 'thumbnail', 'metadata', 'style', 'sld',
                                                                  'access_rights', 'bounding_box', 'native_crs',
                                                                  'native_bounding_box', },
            settings.FILE_TYPE_RASTER: {'name', 'uuid', 'layman_metadata', 'url', 'title', 'description', 'updated_at',
                                        'wms', 'thumbnail', 'file', 'metadata', 'style', 'sld', 'access_rights',
                                        'bounding_box', 'native_crs', 'native_bounding_box', 'image_mosaic', },
            settings.FILE_TYPE_UNKNOWN: {'name', 'uuid', 'layman_metadata', 'url', 'title', 'description', 'updated_at',
                                         'wms', 'thumbnail', 'file', 'metadata', 'style', 'sld', 'access_rights',
                                         'bounding_box', 'native_crs', 'native_bounding_box', },
        },
        'multi_info_keys_to_remove': [],
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


def get_workspace_publication_url(workspace, publication_name):
    return url_for('rest_workspace_layer.get', layername=publication_name, workspace=workspace)
