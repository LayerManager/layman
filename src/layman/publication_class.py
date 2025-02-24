from dataclasses import dataclass
from typing import Tuple, Dict, Any, List

from layman import util


@dataclass(frozen=True, )
class Publication:
    workspace: str
    type: str
    name: str
    uuid: str
    _info: Dict[str, Any]
    access_rights: Dict[str, List[str]]

    def __init__(self, *, uuid: str = None, publ_tuple: Tuple[str, str, str] = None):
        assert uuid is not None or publ_tuple is not None

        context = {'keys': ['id']}
        info = util.get_publication_info(*publ_tuple, context=context) if publ_tuple is not None else util.get_publication_info_by_uuid(uuid=uuid, context=context)

        object.__setattr__(self, 'uuid', info['uuid'])
        object.__setattr__(self, 'workspace', info['_workspace'])
        object.__setattr__(self, 'type', info['type'])
        object.__setattr__(self, 'name', info['name'])
        object.__setattr__(self, 'access_rights', info['access_rights'])
        object.__setattr__(self, '_info', info)
