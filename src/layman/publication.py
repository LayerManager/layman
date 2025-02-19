from dataclasses import dataclass
from typing import List

from db import TableUri
from layman import names, util


@dataclass(frozen=True)
class LaymanPublication:
    # pylint: disable=too-many-instance-attributes
    workspace: str
    publ_type: str
    name: str
    uuid: str
    geodata_type: str
    native_bounding_box: List[float]
    native_crs: str
    table_uri: TableUri

    def __init__(self, *, uuid: str = None,):
        workspace, publ_type, name = util._get_publication_by_uuid(uuid)  # pylint: disable=protected-access
        info = util.get_publication_info(workspace, publ_type, name, context={'keys': ['id']})
        object.__setattr__(self, 'uuid', uuid)
        object.__setattr__(self, 'workspace', workspace)
        object.__setattr__(self, 'publ_type', publ_type)
        object.__setattr__(self, 'name', name)
        object.__setattr__(self, 'geodata_type', info['geodata_type'])
        object.__setattr__(self, 'native_bounding_box', info['native_bounding_box'])
        object.__setattr__(self, 'native_crs', info['native_crs'])
        object.__setattr__(self, 'table_uri', info['_table_uri'])

    @property
    def gs_names(self):
        return names.get_names_by_source(uuid=self.uuid, publication_type=self.publ_type)
