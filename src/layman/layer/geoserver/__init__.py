import json
import re
from urllib.parse import urljoin

import requests
from flask import g, current_app as app

from layman.http import LaymanError
from layman import settings
from layman.common import geoserver as common
from .util import get_layman_users

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
    rolename = common.username_to_rolename(username)
    if username in common.RESERVED_WORKSPACE_NAMES:
        raise LaymanError(35, {'reserved_by': __name__, 'workspace': username})

    if rolename in common.RESERVED_ROLE_NAMES:
        raise LaymanError(35, {'reserved_by': __name__, 'role': rolename})


ensure_whole_user = common.ensure_whole_user


delete_whole_user = common.delete_whole_user


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


get_usernames = get_layman_users


def check_new_layername(username, layername):
    pass
