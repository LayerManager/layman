def get_map_sources():
    return PUBLICATION_TYPES[f'{__name__}']['internal_sources']


MAP_TYPE = __name__


def get_map_type_def():
    return PUBLICATION_TYPES[MAP_TYPE]


from .rest_maps import bp as maps_bp
from .rest_map import bp as map_bp
from .rest_map_file import bp as map_file_bp
from .rest_map_thumbnail import bp as map_thumbnail_bp
from .rest_map_metadata_comparison import bp as map_metadata_comparison_bp

PUBLICATION_TYPES = {
    f'{MAP_TYPE}': {
        'type': MAP_TYPE,
        'module': __name__,
        'blueprints': [
            maps_bp,
            map_bp,
            map_file_bp,
            map_thumbnail_bp,
            map_metadata_comparison_bp,
        ],
        # see also .util.TASKS_TO_MAP_INFO_KEYS
        'internal_sources': [
            'layman.map.filesystem.uuid',
            'layman.map.filesystem.input_file',
            'layman.map.filesystem.thumbnail',
            'layman.map.micka.soap',
            'layman.map.prime_db_schema.table',
        ],
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
