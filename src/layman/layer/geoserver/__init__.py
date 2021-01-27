import json
from urllib.parse import urljoin

import requests
from flask import g

from layman.http import LaymanError
from layman import settings, util as layman_util
from layman.common import geoserver as common
from layman.layer import LAYER_TYPE, db as db_source
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


def check_username(username, auth=settings.LAYMAN_GS_AUTH):
    if username == settings.LAYMAN_GS_USER:
        raise LaymanError(41, {'username': username})

    if username in common.RESERVED_WORKSPACE_NAMES:
        raise LaymanError(35, {'reserved_by': __name__, 'workspace': username})

    rolename = common.username_to_rolename(username)
    if rolename in common.RESERVED_ROLE_NAMES:
        raise LaymanError(35, {'reserved_by': __name__, 'role': rolename})


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
        native_bbox = {
            "minx": -20026376.39,
            "miny": -20048966.10,
            "maxx": 20026376.39,
            "maxy": 20048966.10,
            "crs": "EPSG:3857",
        }
        feature_type_def['nativeBoundingBox'] = native_bbox
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
    # current_app.logger.info(f'publish_layer_from_db before clear_cache {username}')

    if not access_rights or not access_rights.get('read') or not access_rights.get('write'):
        layer_info = layman_util.get_publication_info(workspace, LAYER_TYPE, layername, context={'sources_filter': 'layman.layer.prime_db_schema.table', })

    read_roles = (access_rights and access_rights.get('read')) or layer_info['access_rights']['read']
    write_roles = (access_rights and access_rights.get('write')) or layer_info['access_rights']['write']

    security_read_roles = common.layman_users_to_geoserver_roles(read_roles)
    common.ensure_layer_security_roles(geoserver_workspace, layername, security_read_roles, 'r', settings.LAYMAN_GS_AUTH)

    security_write_roles = common.layman_users_to_geoserver_roles(write_roles)
    common.ensure_layer_security_roles(geoserver_workspace, layername, security_write_roles, 'w', settings.LAYMAN_GS_AUTH)


def get_usernames():
    return common.get_usernames_by_role(settings.LAYMAN_GS_ROLE, settings.LAYMAN_GS_AUTH, [settings.LAYMAN_GS_USER])


def get_workspaces():
    return common.get_all_workspaces(settings.LAYMAN_GS_AUTH)


def check_new_layername(username, layername):
    pass
