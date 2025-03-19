from dataclasses import dataclass
from typing import Tuple, Literal, ClassVar

from db import TableUri
from layman import settings
from layman.publication_class import Publication

from . import LAYER_TYPE
from .db import DbNames
from .geoserver import GeoserverNames
from .qgis import QgisNames
from ..common.micka import MickaNames


@dataclass(frozen=True, )
class Layer(Publication):
    _class_publication_type_for_create: ClassVar[str] = LAYER_TYPE
    _class_init_tuple_name: ClassVar[str] = 'layer_tuple'

    geodata_type: Literal["vector", "raster", "unknown"]
    style_type: str
    original_data_source: settings.EnumOriginalDataSource
    table_uri: TableUri

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

    @property
    def gs_names(self):
        return GeoserverNames(uuid=self.uuid)

    @property
    def qgis_names(self):
        return QgisNames(uuid=self.uuid)

    @property
    def internal_db_names(self):
        return DbNames(uuid=self.uuid)

    @property
    def micka_names(self):
        return MickaNames(uuid=self.uuid)
