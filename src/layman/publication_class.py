from dataclasses import dataclass
from datetime import datetime
from typing import Tuple, Dict, Any, List

from layman import util


@dataclass(frozen=True, )
# pylint: disable=too-many-instance-attributes
class Publication:
    workspace: str
    type: str
    name: str
    uuid: str
    description: str
    title: str
    access_rights: Dict[str, List[str]]
    created_at: datetime
    native_bounding_box: List[float]
    native_crs: str
    _info: Dict[str, Any]

    def __init__(self, *, uuid: str = None, publ_tuple: Tuple[str, str, str] = None):
        assert uuid is not None or publ_tuple is not None

        context = {'keys': ['id']}
        info = util.get_publication_info(*publ_tuple, context=context) if publ_tuple is not None else util.get_publication_info_by_uuid(uuid=uuid, context=context)

        object.__setattr__(self, 'uuid', info['uuid'])
        object.__setattr__(self, 'workspace', info['_workspace'])
        object.__setattr__(self, 'type', info['type'])
        object.__setattr__(self, 'name', info['name'])
        object.__setattr__(self, 'access_rights', info['access_rights'])
        object.__setattr__(self, 'description', info['description'])
        object.__setattr__(self, 'title', info['title'])
        object.__setattr__(self, 'created_at', info['_created_at'])
        object.__setattr__(self, 'native_bounding_box', info['native_bounding_box'])
        object.__setattr__(self, 'native_crs', info['native_crs'])
        object.__setattr__(self, '_info', info)
