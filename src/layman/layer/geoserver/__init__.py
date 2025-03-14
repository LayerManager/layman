import logging
from flask import g

import crs as crs_def
from geoserver import util as gs_util
from layman.http import LaymanError
from layman import settings, util as layman_util
from layman.common import bbox as bbox_util, geoserver as gs_common, empty_method
from . import wms
from .util import get_external_db_store_name
from ..layer_class import Layer

logger = logging.getLogger(__name__)
FLASK_RULES_KEY = f"{__name__}:RULES"

GEOSERVER_NAME_PREFIX = 'l_'
GEOSERVER_WFS_WORKSPACE = 'layman'
GEOSERVER_WMS_WORKSPACE = f'{GEOSERVER_WFS_WORKSPACE}{settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX}'


def ensure_whole_user(username, auth=settings.LAYMAN_GS_AUTH):
    gs_util.ensure_user(username, None, auth)


def delete_whole_user(username, auth=settings.LAYMAN_GS_AUTH):
    gs_util.delete_user(username, auth)


ensure_workspace = empty_method


def create_external_db_store(workspace, *, uuid, table_uri, auth=settings.LAYMAN_GS_AUTH):
    pg_conn = {
        'host': table_uri.hostname,
        'port': table_uri.port,
        'dbname': table_uri.db_name,
        'user': table_uri.username,
        'password': table_uri.password,
    }
    store_name = get_external_db_store_name(uuid=uuid)
    gs_util.create_db_store(workspace,
                            auth,
                            db_schema=table_uri.schema,
                            pg_conn=pg_conn,
                            name=store_name,
                            )
    return store_name


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


def set_security_rules(*, layer: Layer, gs_names, access_rights, auth, ):
    read_roles = access_rights.get('read') if access_rights and access_rights.get('read') else layer.access_rights['read']
    write_roles = access_rights.get('write') if access_rights and access_rights.get('write') else layer.access_rights['write']

    security_read_roles = gs_common.layman_users_and_roles_to_geoserver_roles(read_roles)
    gs_util.ensure_layer_security_roles(gs_names.workspace, gs_names.name, security_read_roles, 'r', auth)

    security_write_roles = gs_common.layman_users_and_roles_to_geoserver_roles(write_roles)
    gs_util.ensure_layer_security_roles(gs_names.workspace, gs_names.name, security_write_roles, 'w', auth)


def get_layer_bbox(*, layer: Layer):
    # GeoServer is not working good with degradeted bbox
    result = bbox_util.get_bbox_to_publish(layer.native_bounding_box, layer.native_crs)
    return result


def publish_layer_from_db(*, layer: Layer, gs_names, metadata_url, store_name=None):
    bbox = get_layer_bbox(layer=layer)
    lat_lon_bbox = bbox_util.transform(bbox, layer.native_crs, crs_def.EPSG_4326)
    gs_util.post_feature_type(gs_names.workspace, gs_names.name, layer.description, layer.title, bbox, layer.native_crs, settings.LAYMAN_GS_AUTH, lat_lon_bbox=lat_lon_bbox, table_name=layer.table_uri.table, metadata_url=metadata_url, store_name=store_name)


def publish_layer_from_qgis(*, layer: Layer, gs_names, metadata_url, ):
    store_name = wms.get_qgis_store_name(uuid=layer.uuid)
    info = layman_util.get_publication_info_by_class(layer, context={'keys': ['wms', ]})
    layer_capabilities_url = info['_wms']['qgis_capabilities_url']
    gs_util.create_wms_store(gs_names.workspace,
                             settings.LAYMAN_GS_AUTH,
                             store_name,
                             layer_capabilities_url)
    bbox = get_layer_bbox(layer=layer)
    lat_lon_bbox = bbox_util.transform(bbox, layer.native_crs, crs_def.EPSG_4326)
    gs_util.post_wms_layer(gs_names.workspace, gs_names.name, layer.qgis_names.name, store_name, layer.title, layer.description, bbox, layer.native_crs, settings.LAYMAN_GS_AUTH,
                           lat_lon_bbox=lat_lon_bbox, metadata_url=metadata_url)


def get_usernames():
    return gs_util.get_usernames_by_role(settings.LAYMAN_GS_ROLE, settings.LAYMAN_GS_AUTH, [settings.LAYMAN_GS_USER])


def get_workspaces():
    all_workspaces = gs_util.get_all_workspaces(settings.LAYMAN_GS_AUTH)
    result = [workspace for workspace in all_workspaces if not workspace.endswith(settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX)]
    return result
