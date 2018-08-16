import json
import os

from .filesystem import get_user_dir
from .http import LaymanError
from .settings import *
from .util import get_layman_rules, get_non_layman_workspaces

headers_json = {
    'Accept': 'application/json',
    'Content-type': 'application/json',
}
headers_xml = {
    'Accept': 'application/xml',
    'Content-type': 'application/xml',
}


def ensure_user_workspace(username):
    # GeoServer workspace name conflicts
    if username in GS_RESERVED_WORKSPACE_NAMES:
        raise LaymanError(13, {'workspace': username})
    r = requests.get(
        LAYMAN_GS_REST_WORKSPACES,
        # data=json.dumps(payload),
        headers=headers_json,
        auth=LAYMAN_GS_AUTH
    )
    r.raise_for_status()
    # app.logger.info(r.text)
    all_workspaces = r.json()['workspaces']['workspace']
    r = requests.get(
        LAYMAN_GS_REST_SECURITY_ACL_LAYERS,
        # data=json.dumps(payload),
        headers=headers_json,
        auth=LAYMAN_GS_AUTH
    )
    r.raise_for_status()
    # app.logger.info(r.text)
    all_rules = r.json()
    layman_rules = get_layman_rules(all_rules)
    non_layman_workspaces = get_non_layman_workspaces(all_workspaces,
                                                      layman_rules)
    if any(ws['name'] == username for ws in non_layman_workspaces):
        raise LaymanError(12, {'workspace': username})
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


def publish_layer_from_db(username, layername, description, title, sld_file):
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
    create_layer_style(username, layername, sld_file)


def create_layer_style(username, layername, sld_file):
    if sld_file is None:
        return
    r = requests.post(
        urljoin(LAYMAN_GS_REST_WORKSPACES, username + '/styles/'),
        data=json.dumps(
            {
                "style": {
                    "name": layername,
                    # "workspace": {
                    #     "name": "browser"
                    # },
                    "format": "sld",
                    # "languageVersion": {
                    #     "version": "1.0.0"
                    # },
                    "filename": layername + ".sld"
                }
            }
        ),
        headers=headers_json,
        auth=LAYMAN_GS_AUTH
    )
    r.raise_for_status()
    # app.logger.info(sld_file.read())
    r = requests.put(
        urljoin(LAYMAN_GS_REST_WORKSPACES, username +
                '/styles/' + layername),
        data=sld_file.read(),
        headers={
            'Accept': 'application/json',
            'Content-type': 'application/vnd.ogc.sld+xml',
        },
        auth=LAYMAN_GS_AUTH
    )
    if r.status_code == 400:
        raise LaymanError(14, data=r.text)
    r.raise_for_status()
    r = requests.put(
        urljoin(LAYMAN_GS_REST_WORKSPACES, username +
                '/layers/' + layername),
        data=json.dumps(
            {
                "layer": {
                    "defaultStyle": {
                        "name": username + ':' + layername,
                        "workspace": username,
                    },
                }
            }
        ),
        headers=headers_json,
        auth=LAYMAN_GS_AUTH
    )
    # app.logger.info(r.text)
    r.raise_for_status()


def generate_layer_thumbnail(username, layername):
    wms_url = urljoin(LAYMAN_GS_URL, username + '/ows')
    userdir = get_user_dir(username)
    from .gs_util import wms_proxy
    wms = wms_proxy(wms_url)
    # app.logger.info(list(wms.contents))
    bbox = list(wms[layername].boundingBox)
    # app.logger.info(bbox)
    min_range = min(bbox[2] - bbox[0], bbox[3] - bbox[1]) / 2
    tn_bbox = (
        (bbox[0] + bbox[2]) / 2 - min_range,
        (bbox[1] + bbox[3]) / 2 - min_range,
        (bbox[0] + bbox[2]) / 2 + min_range,
        (bbox[1] + bbox[3]) / 2 + min_range,
    )
    tn_img = wms.getmap(
        layers=[layername],
        srs='EPSG:3857',
        bbox=tn_bbox,
        size=(300, 300),
        format='image/png',
        transparent=True,
    )
    tn_path = os.path.join(userdir, layername+'.thumbnail.png')
    out = open(tn_path, 'wb')
    out.write(tn_img.read())
    out.close()
    return tn_img