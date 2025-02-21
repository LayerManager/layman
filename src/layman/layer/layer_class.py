from dataclasses import dataclass
from typing import List, Tuple, Dict

from db import TableUri
from layman import names, settings
from layman.publication_class import LaymanPublication

from . import LAYER_TYPE
from .prime_db_schema.table import get_layer_info


@dataclass(frozen=True, )
class LaymanLayer(LaymanPublication):
    geodata_type: str
    style_type: str
    native_bounding_box: List[float]
    native_crs: str
    original_data_source: settings.EnumOriginalDataSource
    table_uri: TableUri
    access_rights: Dict[str, List[str]]

    def __init__(self, *, uuid: str = None, layer_tuple: Tuple[str, str] = None):
        publ_tuple = (layer_tuple[0], LAYER_TYPE, layer_tuple[1]) if layer_tuple else None
        super().__init__(uuid=uuid, publ_tuple=publ_tuple)
        info = get_layer_info(self.workspace, self.name)
        object.__setattr__(self, 'geodata_type', info['geodata_type'])
        object.__setattr__(self, 'style_type', info['_style_type'])
        object.__setattr__(self, 'native_bounding_box', info['native_bounding_box'])
        object.__setattr__(self, 'native_crs', info['native_crs'])
        object.__setattr__(self, 'original_data_source', info['original_data_source'])
        object.__setattr__(self, 'table_uri', info['_table_uri'])
        object.__setattr__(self, 'access_rights', info['access_rights'])

    @property
    def gs_names(self):
        return names.get_names_by_source(uuid=self.uuid, publication_type=self.type)
