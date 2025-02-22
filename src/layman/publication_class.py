from dataclasses import dataclass
from typing import Tuple

from layman import util


@dataclass(frozen=True, )
class Publication:
    workspace: str
    type: str
    name: str
    uuid: str

    def __init__(self, *, uuid: str = None, publ_tuple: Tuple[str, str, str] = None):
        assert uuid is not None or publ_tuple is not None

        workspace, publ_type, name = util._get_publication_by_uuid(uuid) if publ_tuple is None else publ_tuple  # pylint: disable=protected-access
        if uuid is None:
            uuid = util.get_publication_uuid(*publ_tuple)

        object.__setattr__(self, 'uuid', uuid)
        object.__setattr__(self, 'workspace', workspace)
        object.__setattr__(self, 'type', publ_type)
        object.__setattr__(self, 'name', name)
