from dataclasses import dataclass
from typing import List

from db import TableUri
from layman import names
from layman.publication_class import LaymanPublication

from .prime_db_schema.table import get_layer_info


@dataclass(frozen=True, )
class LaymanLayer(LaymanPublication):
    geodata_type: str
    native_bounding_box: List[float]
    native_crs: str
    table_uri: TableUri

    def __init__(self, *, uuid: str,):
        super().__init__(uuid=uuid)
        info = get_layer_info(self.workspace, self.name)
        object.__setattr__(self, 'geodata_type', info['geodata_type'])
        object.__setattr__(self, 'native_bounding_box', info['native_bounding_box'])
        object.__setattr__(self, 'native_crs', info['native_crs'])
        object.__setattr__(self, 'table_uri', info['_table_uri'])

    @property
    def gs_names(self):
        return names.get_names_by_source(uuid=self.uuid, publication_type=self.type)
