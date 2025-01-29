from dataclasses import dataclass

from .layer import LAYER_TYPE
from . import settings


GEOSERVER_WFS_WORKSPACE = 'layman'
GEOSERVER_WMS_WORKSPACE = f'{GEOSERVER_WFS_WORKSPACE}{settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX}'


@dataclass(frozen=True)
class NameForSource:
    workspace: str
    name: str


@dataclass(frozen=True)
class Names:
    wfs: NameForSource
    wms: NameForSource
    sld: NameForSource


def get_names_by_source(*, uuid, publication_type):
    assert publication_type == LAYER_TYPE
    return Names(
        wfs=NameForSource(workspace=GEOSERVER_WFS_WORKSPACE, name=f'l_{uuid}'),
        wms=NameForSource(workspace=GEOSERVER_WMS_WORKSPACE, name=f'l_{uuid}'),
        sld=NameForSource(workspace=GEOSERVER_WMS_WORKSPACE, name=uuid),
    )


def get_layer_names_by_source(*, uuid, ):
    return get_names_by_source(uuid=uuid, publication_type=LAYER_TYPE)
