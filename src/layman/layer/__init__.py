LAYER_TYPE = __name__


def get_layer_type_def():
    return PUBLICATION_TYPES[LAYER_TYPE]


def get_layer_sources():
    return get_layer_type_def()['internal_sources']


from .rest_layers import bp as layers_bp
from .rest_layer import bp as layer_bp
from .rest_layer_chunk import bp as layer_chunk_bp
from .rest_layer_thumbnail import bp as layer_thumbnail_bp
from .rest_layer_metadata_comparison import bp as layer_metadata_comparison_bp

PUBLICATION_TYPES = {
    f'{LAYER_TYPE}': {
        'type': LAYER_TYPE,  # unique type name, same as dict key
        'module': __name__,  # name of module that defines the type
        'blueprints': [  # blueprints to register
            layers_bp,
            layer_bp,
            layer_chunk_bp,
            layer_thumbnail_bp,
            layer_metadata_comparison_bp,
        ],
        # see also .util.TASKS_TO_LAYER_INFO_KEYS
        'internal_sources': [  # internal sources to process when new source is published
            'layman.layer.filesystem.uuid',
            'layman.layer.filesystem.input_chunk',
            'layman.layer.filesystem.input_file',
            'layman.layer.filesystem.input_sld',
            'layman.layer.db.table',
            'layman.layer.geoserver.wfs',
            'layman.layer.geoserver.wms',
            'layman.layer.geoserver.sld',
            'layman.layer.filesystem.thumbnail',
            'layman.layer.micka.soap',
        ],
        'task_modules': [
            'layman.layer.db.tasks',
            'layman.layer.filesystem.tasks',
            'layman.layer.geoserver.tasks',
            'layman.layer.micka.tasks',
        ],
        'layman.common.filesystem': {
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
                'scale_denominator',
                'title',
                'wfs_url',
                'wms_url',
            }
        },
    }
}
