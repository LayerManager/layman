import json
import re
from urllib.parse import urljoin

import requests
from flask import g, current_app as app

from layman.http import LaymanError
from layman import settings, util as layman_util
from layman.common import geoserver as common
from layman.layer import LAYER_TYPE, db as db_source

FLASK_WORKSPACES_KEY = f"{__name__}:WORKSPACES"
FLASK_RULES_KEY = f"{__name__}:RULES"

headers_json = {
    'Accept': 'application/json',
    'Content-type': 'application/json',
}
headers_xml = {
    'Accept': 'application/xml',
    'Content-type': 'application/xml',
}


def get_all_rules(auth):
    key = FLASK_RULES_KEY
    if key not in g:
        r = requests.get(
            settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS,
            # data=json.dumps(payload),
            headers=headers_json,
            auth=auth
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


ensure_whole_user = common.ensure_whole_user


delete_whole_user = common.delete_whole_user


def publish_layer_from_db(username, layername, description, title, access_rights):
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
            "name": username + ":postgresql",
        },
    }
    db_bbox = db_source.get_bbox(username, layername)
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
                              username + '/datastores/postgresql/featuretypes/'),
                      data=json.dumps({
                          "featureType": feature_type_def
                      }),
                      headers=headers_json,
                      auth=settings.LAYMAN_GS_AUTH,
                      )
    r.raise_for_status()
    # current_app.logger.info(f'publish_layer_from_db before clear_cache {username}')
    from . import wms
    from . import wfs
    wfs.clear_cache(username)
    wms.clear_cache(username)

    if not access_rights or not access_rights.get('read') or not access_rights.get('write'):
        layer_info = layman_util.get_publication_info(username, LAYER_TYPE, layername, context={'sources_filter': 'layman.layer.prime_db_schema.table', })

    read_roles = (access_rights and access_rights.get('read')) or layer_info['access_rights']['read']
    write_roles = (access_rights and access_rights.get('write')) or layer_info['access_rights']['write']

    security_read_roles = common.layman_users_to_geoserver_roles(read_roles)
    common.ensure_layer_security_roles(username, layername, security_read_roles, 'r', settings.LAYMAN_GS_AUTH)

    security_write_roles = common.layman_users_to_geoserver_roles(write_roles)
    common.ensure_layer_security_roles(username, layername, security_write_roles, 'w', settings.LAYMAN_GS_AUTH)


def get_usernames():
    return common.get_usernames_by_role(settings.LAYMAN_GS_ROLE, settings.LAYMAN_GS_AUTH, [settings.LAYMAN_GS_USER])


def check_new_layername(username, layername):
    pass
