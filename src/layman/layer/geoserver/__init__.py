import logging
from dataclasses import dataclass

from flask import g

from geoserver import util as gs_util
from layman.http import LaymanError
from layman import settings, uuid as uuid_module
from layman.common import empty_method

logger = logging.getLogger(__name__)
FLASK_RULES_KEY = f"{__name__}:RULES"

GEOSERVER_NAME_PREFIX = 'l_'
GEOSERVER_WFS_WORKSPACE = 'layman'
GEOSERVER_WMS_WORKSPACE = f'{GEOSERVER_WFS_WORKSPACE}{settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX}'


@dataclass(frozen=True)
class GeoserverIdsForSource:
    workspace: str
    name: str


@dataclass(frozen=True)
class GeoserverIds:
    wfs: GeoserverIdsForSource
    wms: GeoserverIdsForSource
    sld: GeoserverIdsForSource

    def __init__(self, *, uuid: str):
        object.__setattr__(self, 'wfs', GeoserverIdsForSource(workspace=GEOSERVER_WFS_WORKSPACE, name=f'{GEOSERVER_NAME_PREFIX}{uuid}'))
        object.__setattr__(self, 'wms', GeoserverIdsForSource(workspace=GEOSERVER_WMS_WORKSPACE, name=f'{GEOSERVER_NAME_PREFIX}{uuid}'))
        object.__setattr__(self, 'sld', GeoserverIdsForSource(workspace=GEOSERVER_WMS_WORKSPACE, name=uuid))


def ensure_whole_user(username, auth=settings.LAYMAN_GS_AUTH):
    gs_util.ensure_user(username, None, auth)


def delete_whole_user(username, auth=settings.LAYMAN_GS_AUTH):
    gs_util.delete_user(username, auth)


ensure_workspace = empty_method
delete_workspace = empty_method


def get_all_rules(auth):
    key = FLASK_RULES_KEY
    if key not in g:
        all_rules = gs_util.get_all_security_acl_rules(auth)
        g.setdefault(key, all_rules)

    return g.get(key)


def check_workspace_name(workspace):
    if workspace == settings.LAYMAN_GS_USER:
        raise LaymanError(41, {'workspace': workspace})

    if workspace in gs_util.RESERVED_WORKSPACE_NAMES:
        raise LaymanError(35, {'reserved_by': __name__, 'workspace': workspace})

    if workspace.endswith(settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX):
        raise LaymanError(45, {'workspace_name': workspace})

    rolename = gs_util.username_to_rolename(workspace)
    if rolename in gs_util.RESERVED_ROLE_NAMES:
        raise LaymanError(35, {'reserved_by': __name__, 'role': rolename})


def get_usernames():
    return gs_util.get_usernames_by_role(settings.LAYMAN_GS_ROLE, settings.LAYMAN_GS_AUTH, [settings.LAYMAN_GS_USER])


def get_workspaces():
    all_workspaces = gs_util.get_all_workspaces(settings.LAYMAN_GS_AUTH)
    result = [workspace for workspace in all_workspaces if not workspace.endswith(settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX)]
    return result


def geoserver_layername_to_uuid(*, geoserver_workspace, geoserver_name):
    result = None
    if geoserver_workspace in [GEOSERVER_WFS_WORKSPACE, GEOSERVER_WMS_WORKSPACE] and geoserver_name.startswith(GEOSERVER_NAME_PREFIX):
        possible_uuid = geoserver_name[len(GEOSERVER_NAME_PREFIX):]
        if uuid_module.is_valid_uuid(maybe_uuid_str=possible_uuid):
            result = possible_uuid
    return result
