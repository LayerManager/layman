from dataclasses import dataclass
from typing import Tuple, ClassVar

from layman.publication_class import Publication

from . import MAP_TYPE


@dataclass(frozen=True, )
class Map(Publication):
    _class_publication_type_for_create: ClassVar[str] = MAP_TYPE
    _class_init_tuple_name: ClassVar[str] = 'map_tuple'

    map_layers: list

    def __init__(self, *, uuid: str = None, map_tuple: Tuple[str, str] = None, load: bool = True):
        publ_tuple = (map_tuple[0], MAP_TYPE, map_tuple[1]) if map_tuple else None
        super().__init__(uuid=uuid, publ_tuple=publ_tuple, load=load)

    def load(self):
        super().load()
        info = self._info
        if info:
            object.__setattr__(self, 'map_layers', info['_map_layers'])
