from dataclasses import dataclass
from typing import Tuple

from layman.layer import LAYER_TYPE
from layman.layer.layer_class import Layer


@dataclass(frozen=True, )
class LayerMock(Layer):
    # pylint: disable=super-init-not-called
    def __init__(self, *, uuid: str, layer_tuple: Tuple[str, str]):
        object.__setattr__(self, 'uuid', uuid)
        object.__setattr__(self, 'workspace', layer_tuple[0])
        object.__setattr__(self, 'type', LAYER_TYPE)
        object.__setattr__(self, 'name', layer_tuple[1])
