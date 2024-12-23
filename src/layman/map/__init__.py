from collections import OrderedDict

from layman.util import url_for
from ..common import InternalSourceTypeDef


def get_map_sources():
    return PUBLICATION_TYPES[f'{__name__}']['internal_sources']


MAP_TYPE = __name__


def get_map_type_def():
    return PUBLICATION_TYPES[MAP_TYPE]


def get_map_info_keys():
    return get_map_type_def()['info_keys']


def get_map_patch_keys():
    return get_map_type_def()['patch_keys']


MAP_REST_PATH_NAME = "maps"


from .rest_workspace_maps import bp as workspace_maps_bp
from .rest_workspace_map import bp as workspace_map_bp
from .rest_workspace_map_file import bp as workspace_map_file_bp
from .rest_workspace_map_thumbnail import bp as workspace_map_thumbnail_bp
from .rest_workspace_map_metadata_comparison import bp as workspace_map_metadata_comparison_bp
from .rest_maps import bp as maps_bp

PUBLICATION_TYPES = {
    f'{MAP_TYPE}': {
        'type': MAP_TYPE,
        'module': __name__,
        'rest_path_name': MAP_REST_PATH_NAME,
        'workspace_blueprints': [
            workspace_maps_bp,
            workspace_map_bp,
            workspace_map_file_bp,
            workspace_map_thumbnail_bp,
            workspace_map_metadata_comparison_bp,
        ],
        'blueprints': [
            maps_bp,
        ],
        # see also .util.TASKS_TO_MAP_INFO_KEYS
        'internal_sources': OrderedDict([
            ('layman.map.filesystem.uuid', InternalSourceTypeDef(info_items=[]),),
            ('layman.map.prime_db_schema.table', InternalSourceTypeDef(info_items=['access_rights', 'name', 'title', 'description', 'uuid',
                                                                                   'bounding_box', 'native_crs', 'native_bounding_box',
                                                                                   'updated_at', 'type', 'id', 'image_mosaic',
                                                                                   'map_layers']),),
            ('layman.map.filesystem.input_file', InternalSourceTypeDef(info_items=['file']),),
            ('layman.map.prime_db_schema.file_data', InternalSourceTypeDef(info_items=[]),),
            ('layman.map.filesystem.thumbnail', InternalSourceTypeDef(info_items=['thumbnail', ]),),
            ('layman.map.micka.soap', InternalSourceTypeDef(info_items=['metadata', ]),),
        ]),
        'task_modules': {
            'layman.map.filesystem.tasks',
            'layman.map.micka.tasks',
            'layman.map.prime_db_schema.tasks',
        },
        'layman.common.filesystem': {
            'publications_dir': 'maps'
        },
        'layman.common.metadata': {
            'syncable_properties': {
                'abstract',
                'extent',
                'graphic_url',
                'identifier',
                'map_endpoint',
                'map_file_endpoint',
                'operates_on',
                'reference_system',
                'revision_date',
                'title',
            }
        },
        'info_keys': {'name', 'uuid', 'layman_metadata', 'url', 'title', 'description', 'updated_at',
                      'thumbnail', 'file', 'metadata', 'access_rights', 'bounding_box', },
        'multi_info_keys_to_remove': ['geodata_type', 'wfs_wms_status', ],
        'patch_keys': ['name', 'uuid', 'url'],
    }
}


def get_workspace_publication_url(workspace, publication_name, *, x_forwarded_items=None):
    return url_for('rest_workspace_map.get', mapname=publication_name, workspace=workspace, x_forwarded_items=x_forwarded_items)
