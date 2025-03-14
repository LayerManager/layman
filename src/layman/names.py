from .layer import LAYER_TYPE
from . import uuid as uuid_module
from .layer.geoserver import GEOSERVER_WFS_WORKSPACE, GEOSERVER_WMS_WORKSPACE, GEOSERVER_NAME_PREFIX, GeoserverNameForSource, GeoserverNames


def get_names_by_source(*, uuid, publication_type):
    assert publication_type == LAYER_TYPE
    return GeoserverNames(
        wfs=GeoserverNameForSource(workspace=GEOSERVER_WFS_WORKSPACE, name=f'{GEOSERVER_NAME_PREFIX}{uuid}'),
        wms=GeoserverNameForSource(workspace=GEOSERVER_WMS_WORKSPACE, name=f'{GEOSERVER_NAME_PREFIX}{uuid}'),
        sld=GeoserverNameForSource(workspace=GEOSERVER_WMS_WORKSPACE, name=uuid),
    )


def get_layer_names_by_source(*, uuid, ):
    return get_names_by_source(uuid=uuid, publication_type=LAYER_TYPE)


def geoserver_layername_to_uuid(*, geoserver_workspace, geoserver_name):
    result = None
    if geoserver_workspace in [GEOSERVER_WFS_WORKSPACE, GEOSERVER_WMS_WORKSPACE] and geoserver_name.startswith(GEOSERVER_NAME_PREFIX):
        possible_uuid = geoserver_name[len(GEOSERVER_NAME_PREFIX):]
        if uuid_module.is_valid_uuid(maybe_uuid_str=possible_uuid):
            result = possible_uuid
    return result
