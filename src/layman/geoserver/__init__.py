import json
import re

import requests
from flask import g

from layman.http import LaymanError
from layman.settings import *

headers_json = {
    'Accept': 'application/json',
    'Content-type': 'application/json',
}
headers_xml = {
    'Accept': 'application/xml',
    'Content-type': 'application/xml',
}


def get_all_workspaces():
    key = 'layman.geoserver.workspaces'
    if key not in g:
        r = requests.get(
            LAYMAN_GS_REST_WORKSPACES,
            # data=json.dumps(payload),
            headers=headers_json,
            auth=LAYMAN_GS_AUTH
        )
        r.raise_for_status()
        # app.logger.info(r.text)
        all_workspaces = r.json()['workspaces']['workspace']
        g.setdefault(key, all_workspaces)

    return g.get(key)


def get_all_rules():
    key = 'layman.geoserver.rules'
    if key not in g:
        r = requests.get(
            LAYMAN_GS_REST_SECURITY_ACL_LAYERS,
            # data=json.dumps(payload),
            headers=headers_json,
            auth=LAYMAN_GS_AUTH
        )
        r.raise_for_status()
        # app.logger.info(r.text)
        all_rules = r.json()
        g.setdefault(key, all_rules)

    return g.get(key)


def check_username(username):
    if username in GS_RESERVED_WORKSPACE_NAMES:
        raise LaymanError(13, {'workspace': username})
    non_layman_workspaces = get_non_layman_workspaces()
    if any(ws['name'] == username for ws in non_layman_workspaces):
        raise LaymanError(12, {'workspace': username})


def ensure_user_workspace(username):
    all_workspaces = get_all_workspaces()
    if not any(ws['name'] == username for ws in all_workspaces):
        r = requests.post(
            LAYMAN_GS_REST_WORKSPACES,
            data=json.dumps({'workspace': {'name': username}}),
            headers=headers_json,
            auth=LAYMAN_GS_AUTH
        )
        r.raise_for_status()
        r = requests.post(
            LAYMAN_GS_REST_SECURITY_ACL_LAYERS,
            data=json.dumps(
                {username + '.*.r': LAYMAN_GS_ROLE + ',ROLE_ANONYMOUS'}),
            headers=headers_json,
            auth=LAYMAN_GS_AUTH
        )
        r.raise_for_status()
        ensure_user_db_store(username)


def ensure_user_db_store(username):
    r = requests.post(
        urljoin(LAYMAN_GS_REST_WORKSPACES, username + '/datastores'),
        data=json.dumps({
            "dataStore": {
                "name": "postgresql",
                "connectionParameters": {
                    "entry": [
                        {
                            "@key": "dbtype",
                            "$": "postgis"
                        },
                        {
                            "@key": "host",
                            "$": LAYMAN_PG_HOST
                        },
                        {
                            "@key": "port",
                            "$": LAYMAN_PG_PORT
                        },
                        {
                            "@key": "database",
                            "$": LAYMAN_PG_DBNAME
                        },
                        {
                            "@key": "user",
                            "$": LAYMAN_PG_USER
                        },
                        {
                            "@key": "passwd",
                            "$": LAYMAN_PG_PASSWORD
                        },
                        {
                            "@key": "schema",
                            "$": username
                        },
                    ]
                },
            }
        }),
        headers=headers_json,
        auth=LAYMAN_GS_AUTH
    )
    r.raise_for_status()


def publish_layer_from_db(username, layername, description, title):
    keywords = [
        "features",
        layername,
        title
    ]
    keywords = list(set(keywords))
    r = requests.post(
        urljoin(LAYMAN_GS_REST_WORKSPACES,
                username + '/datastores/postgresql/featuretypes/'),
        data=json.dumps(
            {
                "featureType": {
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
            }
        ),
        headers=headers_json,
        auth=LAYMAN_GS_AUTH
    )
    r.raise_for_status()


def get_layman_rules(all_rules=None, layman_role=LAYMAN_GS_ROLE):
    if all_rules==None:
        all_rules = get_all_rules()
    re_role = r".*\b" + re.escape(layman_role) + r"\b.*"
    result = {k: v for k, v in all_rules.items() if re.match(re_role, v)}
    return result


def get_non_layman_workspaces(all_workspaces=None, layman_rules=None):
    if all_workspaces==None:
        all_workspaces = get_all_workspaces()
    if layman_rules==None:
        layman_rules = get_layman_rules()
    result = [
        ws for ws in all_workspaces
        if next((
            k for k in layman_rules
            if re.match(r"^" + re.escape(ws['name']) + r"\..*", k)
        ), None) is None
    ]
    return result


def get_layman_workspaces():
    all_workspaces = get_all_workspaces()
    non_layman_workspaces = get_non_layman_workspaces()
    layman_workspaces = filter(lambda ws: ws not in non_layman_workspaces,
                               all_workspaces)
    return layman_workspaces