def get_map_sources():
    return PUBLICATION_TYPES[f'{__name__}']['internal_sources']


from .rest_maps import bp as maps_bp
from .rest_map import bp as map_bp
from .rest_map_file import bp as map_file_bp


MAP_TYPE = __name__


PUBLICATION_TYPES = {
    f'{MAP_TYPE}': {
        'type': MAP_TYPE,
        'module': __name__,
        'blueprints': [
            maps_bp,
            map_bp,
            map_file_bp,
        ],
        'internal_sources': [
            'layman.map.filesystem.uuid',
            'layman.map.filesystem.input_file',
        ],
        'task_modules': [
        ],
        'layman.common.filesystem': {
            'publications_dir': 'maps'
        },
    }
}


