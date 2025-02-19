from dataclasses import dataclass
from layman import util


@dataclass(frozen=True, )
class LaymanPublication:
    workspace: str
    type: str
    name: str
    uuid: str

    def __init__(self, *, uuid: str,):
        workspace, publ_type, name = util._get_publication_by_uuid(uuid)  # pylint: disable=protected-access
        object.__setattr__(self, 'uuid', uuid)
        object.__setattr__(self, 'workspace', workspace)
        object.__setattr__(self, 'type', publ_type)
        object.__setattr__(self, 'name', name)
