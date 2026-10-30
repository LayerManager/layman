from urllib.parse import urljoin

from geoserver import util as gs_util
from layman import settings, patch_mode
from layman.common import empty_method, empty_method_returns_dict
from layman.layer.geoserver import GEOSERVER_WMS_WORKSPACE, GeoserverIds
from .util import get_gs_proxy_server_url

VERSION = '1.0.0'
PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT

get_metadata_comparison = empty_method_returns_dict
pre_publication_action_check = empty_method
post_layer = empty_method
patch_layer = empty_method
delete_layer = empty_method_returns_dict


def get_wcs_url(external_url=False, *, x_forwarded_items=None):
    assert external_url or not x_forwarded_items
    workspace = GEOSERVER_WMS_WORKSPACE
    base_url = get_gs_proxy_server_url(x_forwarded_items=x_forwarded_items) + settings.LAYMAN_GS_PATH \
        if external_url else settings.LAYMAN_GS_URL
    return urljoin(base_url, workspace + '/wcs')


def add_capabilities_params_to_url(url):
    from . import wms
    params = {'SERVICE': 'WCS', 'REQUEST': 'GetCapabilities', 'VERSION': VERSION}
    url = wms.add_params_to_url(url, params)
    return url


def get_capabilities_url():
    url = get_wcs_url(external_url=True)
    url = add_capabilities_params_to_url(url)
    return url


def is_coverage_layer(gs_layer):
    return bool(gs_layer) and gs_layer.get('resource', {}).get('@class') == 'coverage'


def get_layer_info(uuid, *, x_forwarded_items=None):
    if uuid is None:
        return {}
    gs_layername = GeoserverIds(uuid=uuid).wms
    gs_layer = gs_util.get_layer(gs_layername.workspace, gs_layername.name, auth=settings.LAYMAN_GS_AUTH)
    if not is_coverage_layer(gs_layer):
        return {}
    return {
        'wcs': {
            'name': gs_layername.name,
            'url': get_wcs_url(external_url=True, x_forwarded_items=x_forwarded_items),
        },
    }
