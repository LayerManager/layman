import json
from urllib.parse import urljoin
import requests
from flask import g

from layman.http import LaymanError
from layman import settings, util as layman_util
from layman.common import geoserver as common
from layman.layer import LAYER_TYPE, db as db_source
from layman.layer.qgis import wms as qgis_wms
from . import wms

FLASK_RULES_KEY = f"{__name__}:RULES"

headers_json = {
    'Accept': 'application/json',
    'Content-type': 'application/json',
}
headers_xml = {
    'Accept': 'application/xml',
    'Content-type': 'application/xml',
}


def ensure_whole_user(username, auth=settings.LAYMAN_GS_AUTH):
    common.ensure_user(username, None, auth)
    role = common.username_to_rolename(username)
    common.ensure_role(role, auth)
    common.ensure_user_role(username, role, auth)
    common.ensure_user_role(username, settings.LAYMAN_GS_ROLE, auth)
    ensure_workspace(username, auth)


def delete_whole_user(username, auth=settings.LAYMAN_GS_AUTH):
    role = common.username_to_rolename(username)
    delete_workspace(username, auth)
    common.delete_user_role(username, role, auth)
    common.delete_user_role(username, settings.LAYMAN_GS_ROLE, auth)
    common.delete_role(role, auth)
    common.delete_user(username, auth)


def ensure_workspace(workspace, auth=settings.LAYMAN_GS_AUTH):
    geoserver_wms_workspace = wms.get_geoserver_workspace(workspace)
    for ws in [workspace, geoserver_wms_workspace]:
        created = common.ensure_workspace(ws, auth)
        if created:
            common.create_db_store(ws, auth, workspace)


def delete_workspace(workspace, auth=settings.LAYMAN_GS_AUTH):
    geoserver_wms_workspace = wms.get_geoserver_workspace(workspace)
    for ws in [workspace, geoserver_wms_workspace]:
        common.delete_db_store(ws, auth)
        common.delete_workspace(ws, auth)


def get_all_rules(auth):
    key = FLASK_RULES_KEY
    if key not in g:
        r = requests.get(
            settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS,
            # data=json.dumps(payload),
            headers=headers_json,
            auth=auth,
            timeout=5,
        )
        r.raise_for_status()
        # app.logger.info(r.text)
        all_rules = r.json()
        g.setdefault(key, all_rules)

    return g.get(key)


def check_username(username):
    if username == settings.LAYMAN_GS_USER:
        raise LaymanError(41, {'username': username})

    if username in common.RESERVED_WORKSPACE_NAMES:
        raise LaymanError(35, {'reserved_by': __name__, 'workspace': username})

    if username.endswith(settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX):
        raise LaymanError(45, {'workspace_name': username})

    rolename = common.username_to_rolename(username)
    if rolename in common.RESERVED_ROLE_NAMES:
        raise LaymanError(35, {'reserved_by': __name__, 'role': rolename})


def set_security_rules(workspace, layer, access_rights, auth, geoserver_workspace):
    geoserver_workspace = geoserver_workspace or workspace
    layer_info = None
    if not access_rights or not access_rights.get('read') or not access_rights.get('write'):
        layer_info = layman_util.get_publication_info(workspace, LAYER_TYPE, layer,
                                                      context={'keys': ['access_rights', ]})

    read_roles = access_rights.get('read') if access_rights and 'read' in access_rights else layer_info['access_rights']['read']
    write_roles = access_rights.get('write') if access_rights and 'write' in access_rights else layer_info['access_rights']['write']

    security_read_roles = common.layman_users_to_geoserver_roles(read_roles)
    common.ensure_layer_security_roles(geoserver_workspace, layer, security_read_roles, 'r', auth)

    security_write_roles = common.layman_users_to_geoserver_roles(write_roles)
    common.ensure_layer_security_roles(geoserver_workspace, layer, security_write_roles, 'w', auth)


def get_default_native_bbox(workspace, layer):
    return {
        "minx": settings.LAYMAN_DEFAULT_OUTPUT_BBOX[0],
        "miny": settings.LAYMAN_DEFAULT_OUTPUT_BBOX[1],
        "maxx": settings.LAYMAN_DEFAULT_OUTPUT_BBOX[2],
        "maxy": settings.LAYMAN_DEFAULT_OUTPUT_BBOX[3],
        "crs": "EPSG:3857",
    }


def publish_layer_from_db(workspace, layername, description, title, access_rights, geoserver_workspace=None):
    geoserver_workspace = geoserver_workspace or workspace
    keywords = [
        "features",
        layername,
        title
    ]
    keywords = list(set(keywords))
    feature_type_def = {
        "name": layername,
        "title": title,
        "abstract": description,
        "keywords": {
            "string": keywords
        },
        "srs": "EPSG:3857",
        "projectionPolicy": "FORCE_DECLARED",
        "enabled": True,
        "store": {
            "@class": "dataStore",
            "name": geoserver_workspace + ":postgresql",
        },
    }
    db_bbox = db_source.get_bbox(workspace, layername)
    if db_bbox is None:
        # world
        feature_type_def['nativeBoundingBox'] = get_default_native_bbox(workspace, layername)
    r = requests.post(urljoin(settings.LAYMAN_GS_REST_WORKSPACES,
                              geoserver_workspace + '/datastores/postgresql/featuretypes/'),
                      data=json.dumps({
                          "featureType": feature_type_def
                      }),
                      headers=headers_json,
                      auth=settings.LAYMAN_GS_AUTH,
                      timeout=5,
                      )
    r.raise_for_status()

    set_security_rules(workspace, layername, access_rights, settings.LAYMAN_GS_AUTH, geoserver_workspace)


def publish_layer_from_qgis(workspace, layer, description, title, access_rights, geoserver_workspace=None):
    geoserver_workspace = geoserver_workspace or workspace
    store_name = wms.get_qgis_store_name(layer)
    common.create_wms_store(geoserver_workspace,
                            settings.LAYMAN_GS_AUTH,
                            store_name,
                            qgis_wms.get_layer_capabilities_url(workspace, layer))

    keywords = [
        "features",
        layer,
        title
    ]
    keywords = list(set(keywords))
    wms_layer_def = {
        "name": layer,
        "nativeName": layer,
        "title": title,
        "abstract": description,
        "keywords": {
            "string": keywords
        },
        "nativeCRS": "EPSG:3857",
        "srs": "EPSG:3857",
        "projectionPolicy": "NONE",
        "enabled": True,
        "store": {
            "@class": "wmsStore",
            "name": geoserver_workspace + f":{store_name}",
        },
    }
    db_bbox = db_source.get_bbox(workspace, layer)
    wms_layer_def['nativeBoundingBox'] = get_default_native_bbox(workspace, layer) if not db_bbox else {
        "minx": db_bbox[0],
        "miny": db_bbox[1],
        "maxx": db_bbox[2],
        "maxy": db_bbox[3],
        "crs": "EPSG:3857",
    }
    r = requests.post(urljoin(settings.LAYMAN_GS_REST_WORKSPACES,
                              geoserver_workspace + '/wmslayers/'),
                      data=json.dumps({
                          "wmsLayer": wms_layer_def
                      }),
                      headers=headers_json,
                      auth=settings.LAYMAN_GS_AUTH,
                      timeout=5,
                      )
    r.raise_for_status()

    set_security_rules(workspace, layer, access_rights, settings.LAYMAN_GS_AUTH, geoserver_workspace)


def get_usernames():
    return common.get_usernames_by_role(settings.LAYMAN_GS_ROLE, settings.LAYMAN_GS_AUTH, [settings.LAYMAN_GS_USER])


def get_workspaces():
    all_workspaces = common.get_all_workspaces(settings.LAYMAN_GS_AUTH)
    result = [workspace for workspace in all_workspaces if not workspace.endswith(settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX)]
    return result


def check_new_layername(username, layername):
    pass
