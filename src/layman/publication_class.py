from __future__ import annotations
from abc import abstractmethod, ABC
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple, Dict, Any, List, ClassVar, Type

from layman import util


@dataclass(frozen=True, )
# pylint: disable=too-many-instance-attributes
class Publication(ABC):
    _subclasses: ClassVar[Dict[str, Type[Publication]]] = {}
    _class_publication_type_for_create: ClassVar[str]
    _class_init_tuple_name: ClassVar[str]

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

    def __init_subclass__(cls):
        if hasattr(cls, '_class_publication_type_for_create'):
            cls_publication_type = getattr(cls, '_class_publication_type_for_create')
            if cls_publication_type:
                assert cls_publication_type not in Publication._subclasses
                Publication._subclasses[cls_publication_type] = cls

    def __init__(self, *, uuid: str = None, publ_tuple: Tuple[str, str, str] = None, load: bool = True):
        assert uuid is not None or publ_tuple is not None
        if uuid is not None:
            object.__setattr__(self, 'uuid', uuid)
        if publ_tuple is not None:
            object.__setattr__(self, 'workspace', publ_tuple[0])
            object.__setattr__(self, 'type', publ_tuple[1])
            object.__setattr__(self, 'name', publ_tuple[2])

        if load:
            self.load()

    def load(self):
        context = {'keys': ['id']}
        if hasattr(self, 'uuid'):
            info = util.get_publication_info_by_uuid(uuid=self.uuid, context=context)
        else:
            info = util.get_publication_info(self.workspace, self.type, self.name, context=context)

        if info:
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

    @property
    def exists(self):
        if not hasattr(self, '_info'):
            self.load()
        return bool(self._info)

    def __bool__(self):
        return self.exists

    @abstractmethod
    def replace(self, **kwargs) -> Publication:
        raise NotImplementedError

    @classmethod
    def create(cls, *, publ_tuple: Tuple[str, str, str] = None) -> Publication:
        sub_class = cls._subclasses[publ_tuple[1]]
        return sub_class(**{
            # pylint: disable=protected-access
            sub_class._class_init_tuple_name: (publ_tuple[0], publ_tuple[2])
        })
