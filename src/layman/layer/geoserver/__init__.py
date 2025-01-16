import logging
from flask import g

import crs as crs_def
from geoserver import util as gs_util
from layman.http import LaymanError
from layman import settings, util as layman_util
from layman.common import bbox as bbox_util, geoserver as gs_common
from layman.layer import LAYER_TYPE
from . import wms
from .util import get_external_db_store_name

logger = logging.getLogger(__name__)
FLASK_RULES_KEY = f"{__name__}:RULES"


def ensure_whole_user(username, auth=settings.LAYMAN_GS_AUTH):
    gs_util.ensure_user(username, None, auth)
    ensure_workspace(username, auth)


def delete_whole_user(username, auth=settings.LAYMAN_GS_AUTH):
    delete_workspace(username, auth)
    gs_util.delete_user(username, auth)


def ensure_workspace(workspace, auth=settings.LAYMAN_GS_AUTH):
    geoserver_wms_workspace = wms.get_geoserver_workspace(workspace)
    for wspace in [workspace, geoserver_wms_workspace]:
        created = gs_util.ensure_workspace(wspace, auth)
        if created:
            gs_util.create_db_store(wspace, auth, workspace, pg_conn=settings.PG_CONN)


def create_external_db_store(workspace, layer, table_uri, auth=settings.LAYMAN_GS_AUTH):
    pg_conn = {
        'host': table_uri.hostname,
        'port': table_uri.port,
        'dbname': table_uri.db_name,
        'user': table_uri.username,
        'password': table_uri.password,
    }
    store_name = get_external_db_store_name(layer)
    gs_util.create_db_store(workspace,
                            auth,
                            table_uri.schema,
                            pg_conn=pg_conn,
                            name=store_name,
                            )
    return store_name


def delete_workspace(workspace, auth=settings.LAYMAN_GS_AUTH):
    geoserver_wms_workspace = wms.get_geoserver_workspace(workspace)
    for wspace in [workspace, geoserver_wms_workspace]:
        gs_util.delete_db_store(wspace, auth)
        gs_util.delete_workspace(wspace, auth)


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


def set_security_rules(workspace, layer, access_rights, auth, geoserver_workspace):
    geoserver_workspace = geoserver_workspace or workspace
    layer_info = None
    if not access_rights or not access_rights.get('read') or not access_rights.get('write'):
        layer_info = layman_util.get_publication_info(workspace, LAYER_TYPE, layer,
                                                      context={'keys': ['access_rights', ]})

    read_roles = access_rights.get('read') if access_rights and access_rights.get('read') else layer_info['access_rights']['read']
    write_roles = access_rights.get('write') if access_rights and access_rights.get('write') else layer_info['access_rights']['write']

    security_read_roles = gs_common.layman_users_and_roles_to_geoserver_roles(read_roles)
    gs_util.ensure_layer_security_roles(geoserver_workspace, layer, security_read_roles, 'r', auth)

    security_write_roles = gs_common.layman_users_and_roles_to_geoserver_roles(write_roles)
    gs_util.ensure_layer_security_roles(geoserver_workspace, layer, security_write_roles, 'w', auth)


def get_layer_bbox(workspace, layer):
    layer_info = layman_util.get_publication_info(workspace, LAYER_TYPE, layer, context={'keys': ['native_bounding_box', 'native_crs', ]})
    db_bbox = layer_info['native_bounding_box']
    crs = layer_info['native_crs']
    # GeoServer is not working good with degradeted bbox
    result = bbox_util.get_bbox_to_publish(db_bbox, crs)
    return result


def get_layer_native_bbox(workspace, layer):
    bbox = get_layer_bbox(workspace, layer)
    crs = layman_util.get_publication_info(workspace, LAYER_TYPE, layer, context={'keys': ['native_crs']})['native_crs']

    return gs_util.bbox_to_dict(bbox, crs)


def publish_layer_from_db(workspace, layername, description, title, *, crs, table_name, metadata_url, geoserver_workspace=None, store_name=None):
    geoserver_workspace = geoserver_workspace or workspace
    bbox = get_layer_bbox(workspace, layername)
    lat_lon_bbox = bbox_util.transform(bbox, crs, crs_def.EPSG_4326)
    gs_util.post_feature_type(geoserver_workspace, layername, description, title, bbox, crs, settings.LAYMAN_GS_AUTH, lat_lon_bbox=lat_lon_bbox, table_name=table_name, metadata_url=metadata_url, store_name=store_name)


def publish_layer_from_qgis(workspace, layer, description, title, *, metadata_url, geoserver_workspace=None):
    geoserver_workspace = geoserver_workspace or workspace
    store_name = wms.get_qgis_store_name(layer)
    info = layman_util.get_publication_info(workspace, LAYER_TYPE, layer, context={'keys': ['wms', 'native_crs', ]})
    layer_capabilities_url = info['_wms']['qgis_capabilities_url']
    crs = info['native_crs']
    gs_util.create_wms_store(geoserver_workspace,
                             settings.LAYMAN_GS_AUTH,
                             store_name,
                             layer_capabilities_url)
    bbox = get_layer_bbox(workspace, layer)
    lat_lon_bbox = bbox_util.transform(bbox, crs, crs_def.EPSG_4326)
    gs_util.post_wms_layer(geoserver_workspace, layer, store_name, title, description, bbox, crs, settings.LAYMAN_GS_AUTH,
                           lat_lon_bbox=lat_lon_bbox, metadata_url=metadata_url)


def get_usernames():
    return gs_util.get_usernames_by_role(settings.LAYMAN_GS_ROLE, settings.LAYMAN_GS_AUTH, [settings.LAYMAN_GS_USER])


def get_workspaces():
    all_workspaces = gs_util.get_all_workspaces(settings.LAYMAN_GS_AUTH)
    result = [workspace for workspace in all_workspaces if not workspace.endswith(settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX)]
    return result
