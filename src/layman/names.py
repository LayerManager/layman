from .layer import LAYER_TYPE


def get_name_by_source(*, name, publication_type):
    assert publication_type == LAYER_TYPE
    return {
        'wfs': f'{name}',
    }
