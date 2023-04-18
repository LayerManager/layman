from dataclasses import dataclass, field
from enum import Enum
from typing import Union, Callable, List, Dict, Optional

import _pytest.mark

from tests.dynamic_data.publications import common_publications
from tests import Publication, EnumTestTypes, PublicationValues


class RestArgDomain(Enum):
    def __init__(self, raw_value, publ_name_part, other_rest_args=None):
        self.raw_value = raw_value
        self.publ_name_part = publ_name_part
        self.other_rest_args = other_rest_args or {}


class WithChunksDomain(RestArgDomain):
    FALSE = (False, None)
    TRUE = (True, 'chunks')


class CompressDomainBase(RestArgDomain):
    pass


class CompressDomain(CompressDomainBase):
    FALSE = (False, None)
    TRUE = (True, 'zipped')


class StyleFileDomainBase(RestArgDomain):
    def __init__(self, raw_value_tuple, publ_name_part):
        raw_value, style_type = raw_value_tuple
        assert style_type in ['sld', 'qml']
        super().__init__(raw_value, publ_name_part)
        self.style_type = style_type


class RestArgs(Enum):
    WITH_CHUNKS = ('with_chunks', WithChunksDomain)
    COMPRESS = ('compress', CompressDomain, CompressDomainBase)
    STYLE_FILE = ('style_file', None, StyleFileDomainBase)

    def __init__(self, name, domain, base_domain=None):
        self.arg_name = name
        self.domain = domain
        self.base_domain = base_domain or domain


class RestMethod(Enum):
    POST = ('post_publication', 'post')
    PATCH = ('patch_publication', 'patch')

    def __init__(self, function_name, publ_name_part):
        self.function_name = function_name
        self.publ_name_part = publ_name_part


class PublicationByDefinitionBase(Enum):
    def __init__(self, publication_definition, publ_name_part):
        self.publication_definition = publication_definition
        self.publ_name_part = publ_name_part


class LayerByUsedServers(PublicationByDefinitionBase):
    LAYER_VECTOR_SLD = (common_publications.LAYER_VECTOR_SLD, 'vector_sld_layer')
    LAYER_VECTOR_QML = (common_publications.LAYER_VECTOR_QML, 'vector_qml_layer')
    LAYER_RASTER = (common_publications.LAYER_RASTER, 'raster_layer')


class PublicationByUsedServers(PublicationByDefinitionBase):
    LAYER_VECTOR_SLD = LayerByUsedServers.LAYER_VECTOR_SLD.value
    LAYER_VECTOR_QML = LayerByUsedServers.LAYER_VECTOR_QML.value
    LAYER_RASTER = LayerByUsedServers.LAYER_RASTER.value
    MAP = (common_publications.MAP_EMPTY, 'map')


@dataclass(frozen=True)
class Parametrization:
    def __init__(self, values: list):
        object.__setattr__(self, '_values', values)

    @property
    def values_list(self) -> list:
        # pylint: disable=no-member
        return list(self._values)

    @property
    def values_set(self) -> frozenset:
        # pylint: disable=no-member
        return frozenset(self._values)

    @property
    def publication_definition(self) -> Optional[PublicationValues]:
        # pylint: disable=no-member
        val = next((v for v in self._values if isinstance(v, PublicationByDefinitionBase)), None)
        return val.publication_definition if val is not None else None

    @property
    def rest_method(self) -> Optional[RestMethod]:
        # pylint: disable=no-member
        return next((v for v in self._values if isinstance(v, RestMethod)), None)

    @property
    def style_file(self) -> Optional[StyleFileDomainBase]:
        # pylint: disable=no-member
        return next((v for v in self._values if isinstance(v, StyleFileDomainBase)), None)

    @property
    def rest_arg_dict(self) -> Dict[RestArgs, RestArgDomain]:
        # pylint: disable=no-member
        return {
            next(arg for arg in RestArgs if issubclass(type(v), arg.base_domain)): v
            for v in self._values if isinstance(v, RestArgDomain)
        }


@dataclass(frozen=True)
class TestCaseType:
    # pylint: disable=too-many-instance-attributes
    pytest_id: str = None
    publication: Union[Publication, Callable[[dict], Publication]] = None
    publication_type: str = None
    key: str = None
    rest_method: RestMethod = None
    rest_args: dict = field(default_factory=dict)
    params: dict = field(default_factory=dict)
    specific_params: dict = field(default_factory=dict)
    type: EnumTestTypes = EnumTestTypes.OPTIONAL
    specific_types: dict = field(default_factory=dict)
    marks: List[_pytest.mark.structures.Mark] = field(default_factory=list)
    parametrization: Parametrization = None
    post_before_patch_args: dict = field(default_factory=dict)
