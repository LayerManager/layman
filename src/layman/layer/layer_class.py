from __future__ import annotations
from dataclasses import dataclass, fields
from typing import Tuple, Literal, ClassVar

from db import TableUri
from layman import settings
from layman.publication_class import Publication

from . import LAYER_TYPE
from .db import DbIds
from .geoserver import GeoserverIds
from .qgis import QgisIds
from ..common.micka import MickaIds


@dataclass(frozen=True, )
class Layer(Publication):
    _class_publication_type_for_create: ClassVar[str] = LAYER_TYPE
    _class_init_tuple_name: ClassVar[str] = 'layer_tuple'

    geodata_type: Literal["vector", "raster", "unknown"]
    style_type: str
    original_data_source: settings.EnumOriginalDataSource
    table_uri: TableUri
    image_mosaic: bool

    def __init__(self, *, uuid: str = None, layer_tuple: Tuple[str, str] = None, load: bool = True):
        publ_tuple = (layer_tuple[0], LAYER_TYPE, layer_tuple[1]) if layer_tuple else None
        super().__init__(uuid=uuid, publ_tuple=publ_tuple, load=load)

    def load(self):
        super().load()
        info = self._info
        if info:
            object.__setattr__(self, 'geodata_type', info['geodata_type'])
            object.__setattr__(self, 'style_type', info['_style_type'])
            object.__setattr__(self, 'original_data_source',
                               settings.EnumOriginalDataSource(info['original_data_source']))
            object.__setattr__(self, 'table_uri', info['_table_uri'])
            object.__setattr__(self, 'image_mosaic', info['image_mosaic'])

    @property
    def gs_ids(self):
        return GeoserverIds(uuid=self.uuid)

    @property
    def qgis_ids(self):
        return QgisIds(uuid=self.uuid)

    @property
    def internal_db_ids(self):
        return DbIds(uuid=self.uuid)

    @property
    def micka_ids(self):
        return MickaIds(uuid=self.uuid)

    def replace(self, **kwargs) -> Layer:
        other_layer = Layer(uuid=self.uuid, layer_tuple=(self.workspace, self.name), load=False)
        all_fields = [f.name for f in fields(Layer)]
        assert set(kwargs) <= set(all_fields)
        for k in all_fields:
            object.__setattr__(other_layer, k, kwargs.get(k, getattr(self, k)))
        return other_layer
