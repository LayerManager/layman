from .layer import LAYER_TYPE


def get_names_by_source(*, uuid, publication_type):
    assert publication_type == LAYER_TYPE
    return {
        'wfs': f'l_{uuid}',
    }


def get_layer_names_by_source(*, uuid, ):
    return get_names_by_source(uuid=uuid, publication_type=LAYER_TYPE)
