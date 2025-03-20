from __future__ import annotations
from dataclasses import dataclass, fields
from typing import Tuple, ClassVar

from layman.publication_class import Publication

from . import MAP_TYPE
from ..common.micka import MickaIds


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

    @property
    def micka_ids(self):
        return MickaIds(uuid=self.uuid)

    def clone(self, **kwargs) -> Map:
        other_map = Map(uuid=self.uuid, map_tuple=(self.workspace, self.name), load=False)
        all_fields = [f.name for f in fields(Map)]
        assert set(kwargs) <= set(all_fields)
        for k in all_fields:
            object.__setattr__(other_map, k, kwargs.get(k, getattr(self, k)))
        return other_map
