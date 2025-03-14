from dataclasses import dataclass
from typing import Tuple, Literal

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
    geodata_type: Literal["vector", "raster", "unknown"]
    style_type: str
    original_data_source: settings.EnumOriginalDataSource
    table_uri: TableUri
    image_mosaic: bool

    def __init__(self, *, uuid: str = None, layer_tuple: Tuple[str, str] = None):
        publ_tuple = (layer_tuple[0], LAYER_TYPE, layer_tuple[1]) if layer_tuple else None
        super().__init__(uuid=uuid, publ_tuple=publ_tuple)
        info = self._info
        object.__setattr__(self, 'geodata_type', info['geodata_type'])
        object.__setattr__(self, 'style_type', info['_style_type'])
        object.__setattr__(self, 'original_data_source',
                           settings.EnumOriginalDataSource(info['original_data_source']))
        object.__setattr__(self, 'table_uri', info['_table_uri'])
        object.__setattr__(self, 'image_mosaic', info['image_mosaic'])

    @property
    def gs_names(self):
        return names.get_names_by_source(uuid=self.uuid, publication_type=self.type)

    @property
    def qgis_names(self):
        return QgisNames(id=f'l_{self.uuid}', name=self.name)

    @property
    def internal_db_names(self):
        return DbNames(uuid=self.uuid)

    def set_geodata_type(self, geodata_type: Literal["vector", "raster", "unknown"]):
        object.__setattr__(self, 'geodata_type', geodata_type)

    def set_style_type(self, style_type: str):
        object.__setattr__(self, 'style_type', style_type)

    def set_image_mosaic(self, image_mosaic: bool):
        object.__setattr__(self, 'image_mosaic', image_mosaic)
