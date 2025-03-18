from dataclasses import dataclass
from typing import Tuple, Union, ClassVar

from layman.layer import LAYER_TYPE
from layman.layer.layer_class import Layer


@dataclass(frozen=True, )
class LayerMock(Layer):
    _class_publication_type_for_create: ClassVar[str] = ''

    # pylint: disable=super-init-not-called
    def __init__(self, *, uuid: str, layer_tuple: Union[Tuple[str, str], None]):
        layer_tuple = layer_tuple or (None, None)
        object.__setattr__(self, 'uuid', uuid)
        object.__setattr__(self, 'workspace', layer_tuple[0])
        object.__setattr__(self, 'type', LAYER_TYPE)
        object.__setattr__(self, 'name', layer_tuple[1])
