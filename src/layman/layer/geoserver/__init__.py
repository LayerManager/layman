import json
import re
from urllib.parse import urljoin

import requests
from flask import g, current_app as app

from layman.http import LaymanError
from layman import settings

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


def get_all_workspaces():
    key = FLASK_WORKSPACES_KEY
    if key not in g:
        r = requests.get(
            settings.LAYMAN_GS_REST_WORKSPACES,
            # data=json.dumps(payload),
            headers=headers_json,
            auth=settings.LAYMAN_GS_AUTH
        )
        r.raise_for_status()
        if r.json()['workspaces'] == "":
            all_workspaces = []
        else:
            all_workspaces = r.json()['workspaces']['workspace']
        g.setdefault(key, all_workspaces)

    return g.get(key)


def get_all_rules():
    key = FLASK_RULES_KEY
    if key not in g:
        r = requests.get(
            settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS,
            # data=json.dumps(payload),
            headers=headers_json,
            auth=settings.LAYMAN_GS_AUTH
        )
        r.raise_for_status()
        # app.logger.info(r.text)
        all_rules = r.json()
        g.setdefault(key, all_rules)

    return g.get(key)


def check_username(username):
    if username in settings.GS_RESERVED_WORKSPACE_NAMES:
        raise LaymanError(35, {'reserved_by': __name__, 'workspace': username})
    # TODO consider remove / change
    non_layman_workspaces = get_non_layman_workspaces()
    if any(ws['name'] == username for ws in non_layman_workspaces):
        raise LaymanError(35, {'reserved_by': __name__, 'reason': 'GeoServer workspace not assigned to LAYMAN_GS_ROLE'})


def ensure_user_workspace(username):
    all_workspaces = get_all_workspaces()
    if not any(ws['name'] == username for ws in all_workspaces):
        r = requests.post(
            settings.LAYMAN_GS_REST_WORKSPACES,
            data=json.dumps({'workspace': {'name': username}}),
            headers=headers_json,
            auth=settings.LAYMAN_GS_AUTH
        )
        r.raise_for_status()
        r = requests.post(
            settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS,
            data=json.dumps(
                {username + '.*.r': settings.LAYMAN_GS_ROLE + ',ROLE_ANONYMOUS'}),
            headers=headers_json,
            auth=settings.LAYMAN_GS_AUTH
        )
        r.raise_for_status()
        ensure_user_db_store(username)


def delete_user_workspace(username):
    delete_user_db_store(username)
    r = requests.delete(
        urljoin(settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS, username + '.*.r'),
        headers=headers_json,
        auth=settings.LAYMAN_GS_AUTH
    )
    if r.status_code != 404:
        r.raise_for_status()
    r = requests.delete(
        urljoin(settings.LAYMAN_GS_REST_WORKSPACES, username),
        headers=headers_json,
        auth=settings.LAYMAN_GS_AUTH
    )
    if r.status_code != 404:
        r.raise_for_status()


def ensure_user_db_store(username):
    r = requests.post(
        urljoin(settings.LAYMAN_GS_REST_WORKSPACES, username + '/datastores'),
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
                            "$": settings.LAYMAN_PG_HOST
                        },
                        {
                            "@key": "port",
                            "$": settings.LAYMAN_PG_PORT
                        },
                        {
                            "@key": "database",
                            "$": settings.LAYMAN_PG_DBNAME
                        },
                        {
                            "@key": "user",
                            "$": settings.LAYMAN_PG_USER
                        },
                        {
                            "@key": "passwd",
                            "$": settings.LAYMAN_PG_PASSWORD
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
        auth=settings.LAYMAN_GS_AUTH
    )
    r.raise_for_status()


def delete_user_db_store(username):
    r = requests.delete(
        urljoin(settings.LAYMAN_GS_REST_WORKSPACES, username + f'/datastores/{username}'),
        headers=headers_json,
        auth=settings.LAYMAN_GS_AUTH
    )
    if r.status_code != 404:
        r.raise_for_status()


def publish_layer_from_db(username, layername, description, title):
    keywords = [
        "features",
        layername,
        title
    ]
    keywords = list(set(keywords))
    r = requests.post(
        urljoin(settings.LAYMAN_GS_REST_WORKSPACES,
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
        auth=settings.LAYMAN_GS_AUTH
    )
    r.raise_for_status()
    # current_app.logger.info(f'publish_layer_from_db before clear_cache {username}')
    from . import wms
    from . import wfs
    wfs.clear_cache(username)
    wms.clear_cache(username)


def get_layman_rules(all_rules=None, layman_role=settings.LAYMAN_GS_ROLE):
    if all_rules == None:
        all_rules = get_all_rules()
    re_role = r".*\b" + re.escape(layman_role) + r"\b.*"
    result = {k: v for k, v in all_rules.items() if re.match(re_role, v)}
    return result


def get_non_layman_workspaces(all_workspaces=None, layman_rules=None):
    if all_workspaces == None:
        all_workspaces = get_all_workspaces()
    if layman_rules == None:
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


def get_usernames():
    return [
        ws['name'] for ws in get_layman_workspaces()
    ]


def check_new_layername(username, layername):
    pass
