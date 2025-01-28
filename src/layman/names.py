from dataclasses import dataclass

from .layer import LAYER_TYPE


@dataclass(frozen=True)
class NameForSource:
    name: str


@dataclass(frozen=True)
class Names:
    wfs: NameForSource
    wms: NameForSource


def get_names_by_source(*, uuid, publication_type):
    assert publication_type == LAYER_TYPE
    return Names(
        wfs=NameForSource(name=f'l_{uuid}'),
        wms=NameForSource(name=f'l_{uuid}')
    )


def get_layer_names_by_source(*, uuid, ):
    return get_names_by_source(uuid=uuid, publication_type=LAYER_TYPE)
