from collections import OrderedDict

from ..common import InternalSourceTypeDef


def get_map_sources():
    return PUBLICATION_TYPES[f'{__name__}']['internal_sources']


MAP_TYPE = __name__


def get_map_type_def():
    return PUBLICATION_TYPES[MAP_TYPE]


MAP_REST_PATH_NAME = "maps"


from .rest_maps import bp as maps_bp
from .rest_map import bp as map_bp
from .rest_map_file import bp as map_file_bp
from .rest_map_thumbnail import bp as map_thumbnail_bp
from .rest_map_metadata_comparison import bp as map_metadata_comparison_bp

PUBLICATION_TYPES = {
    f'{MAP_TYPE}': {
        'type': MAP_TYPE,
        'module': __name__,
        'rest_path_name': MAP_REST_PATH_NAME,
        'blueprints': [
            maps_bp,
            map_bp,
            map_file_bp,
            map_thumbnail_bp,
            map_metadata_comparison_bp,
        ],
        # see also .util.TASKS_TO_MAP_INFO_KEYS
        'internal_sources': OrderedDict([
            ('layman.map.filesystem.uuid', InternalSourceTypeDef(info_items=[]),),
            ('layman.map.prime_db_schema.table', InternalSourceTypeDef(info_items=['access_rights', 'name', 'title', 'uuid', ]),),
            ('layman.map.filesystem.input_file', InternalSourceTypeDef(info_items=['description', 'file']),),
            ('layman.map.filesystem.thumbnail', InternalSourceTypeDef(info_items=['thumbnail', ]),),
            ('layman.map.micka.soap', InternalSourceTypeDef(info_items=['metadata', ]),),
        ]),
        'task_modules': [
            'layman.map.filesystem.tasks',
            'layman.map.micka.tasks',
        ],
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
    }
}
