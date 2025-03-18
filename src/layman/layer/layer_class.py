from dataclasses import dataclass
from typing import Tuple, Literal, ClassVar

from db import TableUri
from layman import names, settings
from layman.publication_class import Publication

from . import LAYER_TYPE
from .db import DbNames


@dataclass(frozen=True)
class QgisNames:
    id: str  # pylint: disable=invalid-name
    name: str


@dataclass(frozen=True, )
class Layer(Publication):
    _class_publication_type: ClassVar[str] = LAYER_TYPE
    _class_init_tuple_name: ClassVar[str] = 'layer_tuple'

    geodata_type: Literal["vector", "raster", "unknown"]
    style_type: str
    original_data_source: settings.EnumOriginalDataSource
    table_uri: TableUri

    def __init__(self, *, uuid: str = None, layer_tuple: Tuple[str, str] = None):
        publ_tuple = (layer_tuple[0], LAYER_TYPE, layer_tuple[1]) if layer_tuple else None
        super().__init__(uuid=uuid, publ_tuple=publ_tuple)

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
        return names.get_names_by_source(uuid=self.uuid, publication_type=self.type)

    @property
    def qgis_names(self):
        return QgisNames(id=f'l_{self.uuid}', name=f'l_{self.uuid}')

    @property
    def internal_db_names(self):
        return DbNames(uuid=self.uuid)
