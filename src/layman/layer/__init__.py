def get_layer_sources():
    return PUBLICATION_TYPES[f'{__name__}']['internal_sources']


from .rest_layers import bp as layers_bp
from .rest_layer import bp as layer_bp
from .rest_layer_chunk import bp as layer_chunk_bp
from .rest_layer_thumbnail import bp as layer_thumbnail_bp


PUBLICATION_TYPES = {
    f'{__name__}': {
        'type': __name__, # unique type name, same as dict key
        'module': __name__, # name of module that defines the type
        'blueprints': [ # blueprints to register
            layers_bp,
            layer_bp,
            layer_chunk_bp,
            layer_thumbnail_bp,
        ],
        'internal_sources': [ # internal sources to process when new source is published
            'layman.layer.filesystem.uuid',
            'layman.layer.filesystem.input_file',
            'layman.layer.filesystem.input_sld',
            'layman.layer.filesystem.input_chunk',
            'layman.layer.db.table',
            'layman.layer.geoserver.wfs',
            'layman.layer.geoserver.wms',
            'layman.layer.geoserver.sld',
            'layman.layer.filesystem.thumbnail',
        ],
        'task_modules': [
            'layman.layer.db.tasks',
            'layman.layer.filesystem.tasks',
            'layman.layer.geoserver.tasks',
        ]
    }
}


