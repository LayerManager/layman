import io
import logging
import json
from functools import partial
import xml.etree.ElementTree as ET
import secrets
import string
from urllib.parse import urljoin
import requests
from owslib import wms as owslib_wms, wfs as owslib_wfs

from crs import util as crs_util
from . import GS_REST_ROLES, GS_REST_USERS, GS_REST_SECURITY_ACL_LAYERS, GS_REST_WORKSPACES, GS_REST_STYLES, GS_AUTH,\
    GS_REST_WMS_SETTINGS, GS_REST_WFS_SETTINGS, GS_REST_USER, GS_REST_SETTINGS, GS_REST, GS_REST_TIMEOUT
from .error import Error


logger = logging.getLogger(__name__)

FLASK_RULES_KEY = f"{__name__}:RULES"
WMS_VERSION = '1.3.0'
WFS_VERSION = '2.0.0'

COVERAGESTORE_GEOTIFF = 'GeoTIFF'
COVERAGESTORE_IMAGEMOSAIC = 'ImageMosaic'

RESERVED_WORKSPACE_NAMES = [
    'default',
]

RESERVED_ROLE_NAMES = [
    'ROLE_ADMINISTRATOR',
    'ROLE_GROUP_ADMIN',
    'ROLE_AUTHENTICATED',
    'ROLE_ANONYMOUS',
]

headers_json = {
    'Accept': 'application/json',
    'Content-type': 'application/json',
}

headers_xml = {
    'Content-type': 'text/xml',
}

headers_sld = {
    '1.0.0': {
        'Accept': 'application/vnd.ogc.sld+xml',
        'Content-type': 'application/xml',
    },
    '1.1.0': {
        'Accept': 'application/vnd.ogc.se+xml',
        'Content-type': 'application/xml',
    },
}

WMS_SERVICE_TYPE = 'wms'
WFS_SERVICE_TYPE = 'wfs'

SERVICE_TYPES = [
    WMS_SERVICE_TYPE,
    WFS_SERVICE_TYPE,
]


DEFAULT_DB_STORE_NAME = 'postgresql'


def get_roles(auth):
    r_url = GS_REST_ROLES
    response = requests.get(r_url,
                            headers=headers_json,
                            auth=auth,
                            timeout=GS_REST_TIMEOUT,
                            )
    response.raise_for_status()
    return response.json()['roles']


def ensure_role(role, auth):
    roles = get_roles(auth)
    role_exists = role in roles
    if not role_exists:
        logger.info(f"Role {role} does not exist yet, creating.")
        response = requests.post(
            urljoin(GS_REST_ROLES, 'role/' + role),
            headers=headers_json,
            auth=auth,
            timeout=GS_REST_TIMEOUT,
        )
        response.raise_for_status()
    else:
        logger.info(f"Role {role} already exists")
    role_created = not role_exists
    return role_created


def delete_role(role, auth):
    response = requests.delete(
        urljoin(GS_REST_ROLES, 'role/' + role),
        headers=headers_json,
        auth=auth,
        timeout=GS_REST_TIMEOUT,
    )
    role_not_exists = response.status_code == 404
    if not role_not_exists:
        response.raise_for_status()
    role_deleted = not role_not_exists
    return role_deleted


def get_usernames(auth):
    r_url = GS_REST_USERS
    response = requests.get(r_url,
                            headers=headers_json,
                            auth=auth,
                            timeout=GS_REST_TIMEOUT,
                            )
    response.raise_for_status()
    # logger.info(f"users={r.text}")
    usernames = [u['userName'] for u in response.json()['users']]
    return usernames


def ensure_user(user, password, auth):
    usernames = get_usernames(auth)
    user_exists = user in usernames
    if not user_exists:
        logger.info(f"User {user} does not exist yet, creating.")
        if password is None:
            # generate random password
            # https://stackoverflow.com/a/23728630
            password = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(32))
            # we usually don't want to log passwords
            # logger.info(f"User {user}'s automatically generated password is {password}")
        response = requests.post(
            GS_REST_USERS,
            # https://osgeo-org.atlassian.net/browse/GEOS-8486
            # seems as it's not fixed in 2.13.0
            data=json.dumps({
                "org.geoserver.rest.security.xml.JaxbUser": {
                    "userName": user,
                    "password": password,
                    "enabled": True,
                },
            }),
            headers=headers_json,
            auth=auth,
            timeout=GS_REST_TIMEOUT,
        )
        response.raise_for_status()
    else:
        logger.info(f"User {user} already exists")
    user_created = not user_exists
    return user_created


def get_workspace_security_roles(workspace, type, auth):
    return get_security_roles(workspace + '.*.' + type, auth)


def get_security_roles(rule, auth):
    response = requests.get(
        GS_REST_SECURITY_ACL_LAYERS,
        headers=headers_json,
        auth=auth,
        timeout=GS_REST_TIMEOUT,
    )
    response.raise_for_status()
    rules = response.json()
    try:
        roles_string = rules[rule]
        roles = set(roles_string.split(','))
    except KeyError:
        roles = set()
    return roles


def get_all_security_acl_rules(auth):
    response = requests.get(
        GS_REST_SECURITY_ACL_LAYERS,
        headers=headers_json,
        auth=auth,
        timeout=GS_REST_TIMEOUT,
    )
    response.raise_for_status()
    all_rules = response.json()
    return all_rules


def ensure_security_roles(rule, roles, auth):
    roles_str = ', '.join(roles)

    logger.info(f"Ensure_security_roles rule={rule}, roles={roles}, roles_str={roles_str}")
    delete_security_roles(rule, auth)

    response = requests.post(
        GS_REST_SECURITY_ACL_LAYERS,
        data=json.dumps(
            {rule: roles_str}),
        headers=headers_json,
        auth=auth,
        timeout=GS_REST_TIMEOUT,
    )
    if response.status_code == 409:
        existing_roles = get_security_roles(rule, auth)
        assert existing_roles == roles, f'existing_roles={existing_roles}, roles={roles}'
    else:
        response.raise_for_status()


def ensure_workspace_security_roles(workspace, roles, type, auth):
    rule = workspace + '.*.' + type
    ensure_security_roles(rule, roles, auth)


def ensure_layer_security_roles(workspace, layername, roles, type, auth):
    rule = f"{workspace}.{layername}.{type}"
    ensure_security_roles(rule, roles, auth)


def delete_feature_type(geoserver_workspace, feature_type_name, auth):
    response = requests.delete(
        urljoin(GS_REST_WORKSPACES,
                geoserver_workspace + f'/datastores/{DEFAULT_DB_STORE_NAME}/featuretypes/' + feature_type_name),
        headers=headers_json,
        auth=auth,
        params={
            'recurse': 'true'
        },
        timeout=GS_REST_TIMEOUT,
    )
    if response.status_code != 404:
        response.raise_for_status()


def patch_feature_type(geoserver_workspace, feature_type_name, *, title=None, description=None, bbox=None, crs=None, auth, lat_lon_bbox=None):
    assert (bbox is None) == (crs is None), f'bbox={bbox}, crs={crs}'
    ftype = dict()

    if title is not None:
        ftype['title'] = title
        keywords = [
            "features",
            feature_type_name,
            title
        ]
        keywords = list(set(keywords))
        ftype['keywords'] = {
            "string": keywords
        }
    if description is not None:
        ftype['abstract'] = description
    if bbox:
        ftype['nativeBoundingBox'] = bbox_to_dict(bbox, crs)
    if lat_lon_bbox:
        ftype['latLonBoundingBox'] = bbox_to_dict(lat_lon_bbox, 'CRS:84')

    ftype = {k: v for k, v in ftype.items() if v is not None}
    body = {
        "featureType": ftype
    }
    response = requests.put(
        urljoin(GS_REST_WORKSPACES,
                geoserver_workspace + '/datastores/postgresql/featuretypes/' + feature_type_name),
        data=json.dumps(body),
        headers=headers_json,
        auth=auth,
        timeout=GS_REST_TIMEOUT,
    )
    response.raise_for_status()


def post_feature_type(geoserver_workspace, layername, description, title, bbox, crs, auth, *, lat_lon_bbox, table_name):
    keywords = [
        "features",
        layername,
        title
    ]
    keywords = list(set(keywords))
    feature_type_def = {
        "name": layername,
        'nativeName': table_name,
        "title": title,
        "abstract": description,
        "keywords": {
            "string": keywords
        },
        "srs": crs,
        "projectionPolicy": "FORCE_DECLARED",
        "enabled": True,
        "store": {
            "@class": "dataStore",
            "name": geoserver_workspace + ":postgresql",
        },
        'nativeBoundingBox': bbox_to_dict(bbox, crs),
        'latLonBoundingBox': bbox_to_dict(lat_lon_bbox, 'CRS:84'),
    }
    response = requests.post(urljoin(GS_REST_WORKSPACES,
                                     geoserver_workspace + '/datastores/postgresql/featuretypes/'),
                             data=json.dumps({
                                 "featureType": feature_type_def
                             }),
                             headers=headers_json,
                             auth=auth,
                             timeout=GS_REST_TIMEOUT,
                             )
    response.raise_for_status()


def delete_security_roles(rule, auth):
    response = requests.delete(
        urljoin(GS_REST_SECURITY_ACL_LAYERS, rule),
        headers=headers_json,
        auth=auth,
        timeout=GS_REST_TIMEOUT,
    )
    if response.status_code != 404:
        response.raise_for_status()


def get_all_workspaces(auth):
    response = requests.get(
        GS_REST_WORKSPACES,
        headers=headers_json,
        auth=auth,
        timeout=GS_REST_TIMEOUT,
    )
    response.raise_for_status()
    if response.json()['workspaces'] == "":
        all_workspaces = []
    else:
        all_workspaces = [workspace["name"] for workspace in response.json()['workspaces']['workspace']]

    return all_workspaces


def get_workspace_layer_url(geoserver_workspace, layer=None):
    layer = layer or ''
    return urljoin(GS_REST_WORKSPACES,
                   geoserver_workspace + '/layers/' + layer)


def get_workspace_style_url(geoserver_workspace, style=None):
    style = style or ''
    return urljoin(GS_REST_WORKSPACES,
                   geoserver_workspace + '/styles/' + style)


def post_workspace_sld_style(geoserver_workspace, layername, sld_file, launder_function):
    if sld_file is None:
        response = requests.get(
            urljoin(GS_REST_STYLES, 'generic.sld'),
            auth=GS_AUTH,
            timeout=GS_REST_TIMEOUT,
        )
        response.raise_for_status()
        sld_file = io.BytesIO(response.content)
    response = requests.post(
        get_workspace_style_url(geoserver_workspace),
        data=f"<style><name>{layername}</name><filename>{layername}.sld</filename></style>",
        headers=headers_xml,
        auth=GS_AUTH,
        timeout=GS_REST_TIMEOUT,
    )
    response.raise_for_status()

    tree = ET.parse(sld_file)
    root = tree.getroot()
    if 'version' in root.attrib and root.attrib['version'] == '1.1.0':
        sld_content_type = 'application/vnd.ogc.se+xml'
    else:
        sld_content_type = 'application/vnd.ogc.sld+xml'

    propertname_els = tree.findall('.//{http://www.opengis.net/ogc}PropertyName')
    if launder_function:
        for element in propertname_els:
            element.text = launder_function(element.text)

    sld_file = io.BytesIO()
    tree.write(
        sld_file,
        encoding=None,
        xml_declaration=True,
    )
    sld_file.seek(0)

    response = requests.put(
        get_workspace_style_url(geoserver_workspace, layername),
        data=sld_file.read(),
        headers={
            'Accept': 'application/json',
            'Content-type': sld_content_type,
        },
        auth=GS_AUTH,
        timeout=GS_REST_TIMEOUT,
    )
    if response.status_code == 400:
        raise Error(1, data=response.text)
    response.raise_for_status()
    response = requests.put(get_workspace_layer_url(geoserver_workspace, layername),
                            data=json.dumps(
                                {
                                    "layer": {
                                        "defaultStyle": {
                                            "name": geoserver_workspace + ':' + layername,
                                            "workspace": geoserver_workspace,
                                        },
                                    }
                                }),
                            headers=headers_json,
                            auth=GS_AUTH,
                            timeout=GS_REST_TIMEOUT,
                            )
    # app.logger.info(r.text)
    response.raise_for_status()


def get_workspace_style_response(geoserver_workspace, stylename, headers=None, auth=None):
    if headers is None:
        response = get_workspace_style_json(geoserver_workspace, stylename, auth)
        if response.status_code == 200:
            style_dict = json.loads(response.content)
            version = style_dict['style']['languageVersion']['version']
        else:
            version = '1.0.0'
        headers = headers_sld[version]
    url = get_workspace_style_url(geoserver_workspace, stylename)
    response = requests.get(url,
                            auth=auth,
                            headers=headers,
                            timeout=GS_REST_TIMEOUT,
                            )
    return response


def get_workspace_style_json(geoserver_workspace, stylename, auth=None):
    url = get_workspace_style_url(geoserver_workspace, stylename)
    response = requests.get(url,
                            auth=auth,
                            headers=headers_json,
                            timeout=GS_REST_TIMEOUT,
                            )
    return response


def delete_workspace_style(geoserver_workspace, stylename, auth=None):
    response = get_workspace_style_response(geoserver_workspace, stylename, auth=auth)
    if response.status_code == 404:
        return {}
    response.raise_for_status()
    sld_stream = io.BytesIO(response.content)

    style_url = get_workspace_style_url(geoserver_workspace, stylename)
    response = requests.delete(style_url,
                               headers=headers_json,
                               auth=GS_AUTH,
                               params={
                                   'purge': 'true',
                                   'recurse': 'true',
                               },
                               timeout=GS_REST_TIMEOUT,
                               )
    if response.status_code == 404:
        return {}
    response.raise_for_status()
    return sld_stream


def create_db_store(geoserver_workspace, auth, db_schema=None, pg_conn=None, name=DEFAULT_DB_STORE_NAME):
    db_schema = db_schema or geoserver_workspace
    response = requests.post(
        urljoin(GS_REST_WORKSPACES, geoserver_workspace + '/datastores'),
        data=json.dumps({
            "dataStore": {
                "name": name,
                "connectionParameters": {
                    "entry": [
                        {
                            "@key": "dbtype",
                            "$": "postgis"
                        },
                        {
                            "@key": "host",
                            "$": pg_conn['host']
                        },
                        {
                            "@key": "port",
                            "$": pg_conn['port']
                        },
                        {
                            "@key": "database",
                            "$": pg_conn['dbname']
                        },
                        {
                            "@key": "user",
                            "$": pg_conn['user']
                        },
                        {
                            "@key": "passwd",
                            "$": pg_conn['password']
                        },
                        {
                            "@key": "schema",
                            "$": db_schema
                        },
                    ]
                },
            }
        }),
        headers=headers_json,
        auth=auth,
        timeout=GS_REST_TIMEOUT,
    )
    response.raise_for_status()


def delete_db_store(geoserver_workspace, auth, *, store_name=DEFAULT_DB_STORE_NAME):
    response = requests.delete(
        urljoin(GS_REST_WORKSPACES, geoserver_workspace + f'/datastores/{store_name}'),
        headers=headers_json,
        auth=auth,
        timeout=GS_REST_TIMEOUT,
    )
    if response.status_code != 404:
        response.raise_for_status()


def patch_coverage(geoserver_workspace, layer, coverage_store, *, title=None, description=None, bbox=None, crs=None,
                   auth, lat_lon_bbox=None):
    assert (bbox is None) == (crs is None), f'bbox={bbox}, crs={crs}'
    coverage = dict()

    if title is not None:
        coverage['title'] = title
        keywords = [
            "features",
            layer,
            title
        ]
        keywords = list(set(keywords))
        coverage['keywords'] = {
            "string": keywords
        }
    if description is not None:
        coverage['abstract'] = description
    if bbox:
        coverage['nativeBoundingBox'] = bbox_to_dict(bbox, crs)
    if lat_lon_bbox:
        coverage['latLonBoundingBox'] = bbox_to_dict(lat_lon_bbox, 'CRS:84')

    coverage = {k: v for k, v in coverage.items() if v is not None}
    body = {
        "coverage": coverage
    }
    response = requests.put(
        urljoin(GS_REST_WORKSPACES,
                geoserver_workspace + f'/coveragestores/{coverage_store}/coverages/{layer}'),
        data=json.dumps(body),
        headers=headers_json,
        auth=auth,
        timeout=GS_REST_TIMEOUT,
    )
    response.raise_for_status()


def create_coverage_store(geoserver_workspace, auth, name, file_or_dir, *, coverage_type=None):
    coverage_type = coverage_type or COVERAGESTORE_GEOTIFF
    data = {
        "coverageStore": {
            "workspace": geoserver_workspace,
            "name": name,
            "type": coverage_type,
            "enabled": "true",
            "url": "file:" + file_or_dir,
        }
    }
    response = requests.post(
        urljoin(GS_REST_WORKSPACES, geoserver_workspace + '/coveragestores'),
        data=json.dumps(data),
        headers=headers_json,
        auth=auth,
        timeout=GS_REST_TIMEOUT,
    )
    response.raise_for_status()


def delete_coverage_store(geoserver_workspace, auth, name):
    response = requests.delete(
        urljoin(GS_REST_WORKSPACES, geoserver_workspace + f'/coveragestores/{name}'),
        headers=headers_json,
        params={
            'purge': 'true',
            'recurse': 'true',
        },
        auth=auth,
        timeout=GS_REST_TIMEOUT,
    )
    if response.status_code != 404:
        response.raise_for_status()


def publish_coverage(geoserver_workspace, auth, coverage_store, layer, title, description, bbox, crs, *, lat_lon_bbox, enable_time_dimension=False):
    keywords = [
        "features",
        layer,
        title
    ]
    native_bbox = bbox_to_dict(bbox, crs)
    data = {
        "coverage": {
            "abstract": description,
            "enabled": "true",
            "keywords": {
                "string": keywords
            },
            "name": layer,
            'nativeBoundingBox': native_bbox,
            "latLonBoundingBox": bbox_to_dict(lat_lon_bbox, 'CRS:84'),
            "nativeFormat": "GeoTIFF",
            "srs": crs,
            "store": {
                "@class": "coverageStore",
                "href": urljoin(GS_REST_WORKSPACES, geoserver_workspace,
                                f'/coveragestores/coverages/{coverage_store}.json'),
                "name": f"{geoserver_workspace}:{coverage_store}"
            },
            "title": title,
        }
    }
    if enable_time_dimension:
        data['coverage']['metadata'] = {
            "entry": [
                {
                    "@key": "elevation",
                    "dimensionInfo": {
                        "enabled": False
                    }
                },
                {
                    "@key": "time",
                    "dimensionInfo": {
                        "enabled": True,
                        "presentation": "LIST",
                        "units": "ISO8601",
                        "defaultValue": {
                            "strategy": "MAXIMUM"
                        },
                        "nearestMatchEnabled": False
                    }
                }
            ]
        }
    response = requests.post(
        urljoin(GS_REST_WORKSPACES, geoserver_workspace + f'/coverages'),
        data=json.dumps(data),
        headers=headers_json,
        auth=auth,
        timeout=GS_REST_TIMEOUT,
    )
    response.raise_for_status()


def create_wms_store(geoserver_workspace, auth, wms_store_name, get_capabilities_url):
    response = requests.post(
        urljoin(GS_REST_WORKSPACES, geoserver_workspace + '/wmsstores'),
        data=json.dumps({
            "wmsStore": {
                "name": wms_store_name,
                "type": "WMS",
                "capabilitiesURL": get_capabilities_url,
            }
        }),
        headers=headers_json,
        auth=auth,
        timeout=GS_REST_TIMEOUT,
    )
    response.raise_for_status()


def delete_wms_store(geoserver_workspace, auth, wms_store_name):
    url = urljoin(GS_REST_WORKSPACES, geoserver_workspace + f'/wmsstores/{wms_store_name}')
    response = requests.delete(
        url,
        headers=headers_json,
        auth=auth,
        timeout=GS_REST_TIMEOUT,
    )
    if response.status_code != 404:
        response.raise_for_status()


def delete_wms_layer(geoserver_workspace, layer, auth):
    url = urljoin(GS_REST_WORKSPACES, geoserver_workspace + f'/wmslayers/{layer}')
    response = requests.delete(
        url,
        headers=headers_json,
        auth=auth,
        timeout=GS_REST_TIMEOUT,
        params={
            'recurse': 'true'
        }
    )
    if response.status_code != 404:
        response.raise_for_status()


def patch_wms_layer(geoserver_workspace, layer, *, auth, bbox=None, title=None, description=None, crs=None, lat_lon_bbox=None):
    wms_layer = get_wms_layer(geoserver_workspace, layer, auth=auth)
    assert (bbox is None) == (crs is None), f'bbox={bbox}, crs={crs}'
    if bbox:
        wms_layer['nativeBoundingBox'] = bbox_to_dict(bbox, crs)
        wms_layer['nativeCRS'] = crs
    if lat_lon_bbox:
        wms_layer['latLonBoundingBox'] = bbox_to_dict(lat_lon_bbox, 'CRS:84')
        # automatically recalculates also 'latLonBoundingBox'
    if title is not None:
        wms_layer['title'] = title
        keywords = [
            "features",
            layer,
            title
        ]
        keywords = list(set(keywords))
        wms_layer['keywords'] = {
            "string": keywords
        }
    if description is not None:
        wms_layer['abstract'] = description

    response = requests.put(urljoin(GS_REST_WORKSPACES,
                            f'{geoserver_workspace}/wmslayers/{layer}'),
                            data=json.dumps({
                                "wmsLayer": wms_layer
                            }),
                            headers=headers_json,
                            auth=auth,
                            timeout=GS_REST_TIMEOUT,
                            )
    response.raise_for_status()


def post_wms_layer(geoserver_workspace, layer, store_name, title, description, bbox, crs, auth, *, lat_lon_bbox):
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
        "nativeCRS": crs,
        "srs": crs,
        "projectionPolicy": "NONE",
        "enabled": True,
        "store": {
            "@class": "wmsStore",
            "name": geoserver_workspace + f":{store_name}",
        },
        'nativeBoundingBox': bbox_to_dict(bbox, crs),
        'latLonBoundingBox': bbox_to_dict(lat_lon_bbox, 'CRS:84'),
    }
    response = requests.post(urljoin(GS_REST_WORKSPACES,
                                     geoserver_workspace + '/wmslayers/'),
                             data=json.dumps({
                                 "wmsLayer": wms_layer_def
                             }),
                             headers=headers_json,
                             auth=auth,
                             timeout=GS_REST_TIMEOUT,
                             )
    response.raise_for_status()


def get_wms_layer(geoserver_workspace, layer, *, auth):
    response = requests.get(urljoin(GS_REST_WORKSPACES,
                            f'{geoserver_workspace}/wmslayers/{layer}'),
                            headers=headers_json,
                            auth=auth,
                            timeout=GS_REST_TIMEOUT,
                            )
    response.raise_for_status()
    return response.json()['wmsLayer']


def ensure_workspace(geoserver_workspace, auth=None):
    auth = auth or GS_AUTH
    all_workspaces = get_all_workspaces(auth)
    if geoserver_workspace not in all_workspaces:
        response = requests.post(
            GS_REST_WORKSPACES,
            data=json.dumps({'workspace': {'name': geoserver_workspace}}),
            headers=headers_json,
            auth=auth,
            timeout=GS_REST_TIMEOUT,
        )
        if response.status_code == 409:
            # if GS returns 409, it seems that workspace was just created by concurrent request
            all_workspaces = get_all_workspaces(auth)
            assert geoserver_workspace in all_workspaces
            return False
        response.raise_for_status()
        return True
    return False


def delete_workspace(geoserver_workspace, auth=None):
    auth = auth or GS_AUTH
    delete_security_roles(geoserver_workspace + '.*.r', auth)
    delete_security_roles(geoserver_workspace + '.*.w', auth)

    response = requests.delete(
        urljoin(GS_REST_WORKSPACES, geoserver_workspace),
        headers=headers_json,
        auth=auth,
        timeout=GS_REST_TIMEOUT,
    )
    if response.status_code != 404:
        response.raise_for_status()


def username_to_rolename(username):
    return f"USER_{username.upper()}"


def delete_user(user, auth):
    r_url = urljoin(GS_REST_USER, user)
    response = requests.delete(
        r_url,
        headers=headers_json,
        auth=auth,
        timeout=GS_REST_TIMEOUT,
    )
    user_not_exists = response.status_code == 404
    if not user_not_exists:
        response.raise_for_status()
    user_deleted = not user_not_exists
    return user_deleted


def get_usernames_by_role(role, auth, usernames_to_ignore=None):
    usernames_to_ignore = usernames_to_ignore or []
    all_usernames = get_usernames(auth)
    usernames = set()
    for user in all_usernames:
        roles = get_user_roles(user, auth)
        if role in roles and user not in usernames_to_ignore:
            usernames.add(user)
    return usernames


def get_user_roles(user, auth):
    r_url = urljoin(GS_REST_ROLES, f'user/{user}/')
    response = requests.get(r_url,
                            headers=headers_json,
                            auth=auth,
                            timeout=GS_REST_TIMEOUT,
                            )
    response.raise_for_status()
    return response.json()['roles']


def ensure_user_role(user, role, auth):
    roles = get_user_roles(user, auth)
    association_exists = role in roles
    if not association_exists:
        logger.info(f"Role {role} not associated with user {user} yet, associating.")
        r_url = urljoin(GS_REST_ROLES, f'role/{role}/user/{user}/')
        response = requests.post(
            r_url,
            headers=headers_json,
            auth=auth,
            timeout=GS_REST_TIMEOUT,
        )
        response.raise_for_status()
    else:
        logger.info(f"Role {role} already associated with user {user}")
    association_created = not association_exists
    return association_created


def delete_user_role(user, role, auth):
    r_url = urljoin(GS_REST_ROLES, f'role/{role}/user/{user}/')
    response = requests.delete(
        r_url,
        headers=headers_json,
        auth=auth,
        timeout=GS_REST_TIMEOUT,
    )
    association_not_exists = response.status_code == 404
    if not association_not_exists:
        response.raise_for_status()
    association_deleted = not association_not_exists
    return association_deleted


def get_service_url(service):
    return {
        WMS_SERVICE_TYPE: GS_REST_WMS_SETTINGS,
        WFS_SERVICE_TYPE: GS_REST_WFS_SETTINGS,
    }[service]


def get_service_settings(service, auth):
    r_url = get_service_url(service)
    response = requests.get(r_url,
                            headers=headers_json,
                            auth=auth,
                            timeout=GS_REST_TIMEOUT,
                            )
    response.raise_for_status()
    return response.json()[service]


get_wms_settings = partial(get_service_settings, WMS_SERVICE_TYPE)
get_wfs_settings = partial(get_service_settings, WFS_SERVICE_TYPE)


def get_service_srs_list(service, auth, service_settings=None):
    if service_settings is None:
        service_settings = get_service_settings(service, auth)
    return service_settings.get('srs', {}).get('string', [])


get_wms_srs_list = partial(get_service_srs_list, WMS_SERVICE_TYPE)
# Maybe it's needed to call /reload after the change in WFS SRS list
get_wfs_srs_list = partial(get_service_srs_list, WFS_SERVICE_TYPE)


def ensure_service_srs_list(service, srs_list, auth):
    srs_list = [get_epsg_code(crs) for crs in srs_list]
    # Maybe it's needed to call /reload after the change in WFS SRS list
    service_settings = get_service_settings(service, auth)
    current_srs_list = get_service_srs_list(service, auth, service_settings=service_settings)
    list_change = set(current_srs_list) != set(srs_list)
    if list_change:
        service_settings['srs'] = {
            'string': srs_list,
        }
        logger.info(f"Service {service}: Current SRS list {current_srs_list} not equals to requested {srs_list}, changing.")
        r_url = get_service_url(service)
        response = requests.put(
            r_url,
            data=json.dumps({
                service: service_settings,
            }),
            headers=headers_json,
            auth=auth,
            timeout=GS_REST_TIMEOUT,
        )
        response.raise_for_status()
    else:
        logger.info(f"Service {service}: Current SRS list {current_srs_list} already corresponds with requested one.")
    return list_change


ensure_wms_srs_list = partial(ensure_service_srs_list, WMS_SERVICE_TYPE)
ensure_wfs_srs_list = partial(ensure_service_srs_list, WFS_SERVICE_TYPE)


def get_global_settings(auth):
    r_url = GS_REST_SETTINGS
    response = requests.get(r_url,
                            headers=headers_json,
                            auth=auth,
                            timeout=GS_REST_TIMEOUT,
                            )
    response.raise_for_status()
    return response.json()['global']


def get_proxy_base_url(auth, global_settings=None):
    if global_settings is None:
        global_settings = get_global_settings(auth)
    return global_settings['settings'].get('proxyBaseUrl', None)


def ensure_proxy_base_url(proxy_base_url, auth):
    global_settings = get_global_settings(auth)
    current_url = get_proxy_base_url(auth, global_settings=global_settings)
    url_equals = proxy_base_url == current_url
    if not url_equals:
        global_settings['settings']['proxyBaseUrl'] = proxy_base_url
        logger.info(f"Current Proxy Base URL {current_url} not equals to requested {proxy_base_url}, changing.")
        r_url = GS_REST_SETTINGS
        response = requests.put(
            r_url,
            data=json.dumps({
                'global': global_settings
            }),
            headers=headers_json,
            auth=auth,
            timeout=GS_REST_TIMEOUT,
        )
        response.raise_for_status()
    else:
        logger.info(f"Current Proxy Base URL {current_url} already corresponds with requested one.")
    url_changed = not url_equals
    return url_changed


def reset(auth):
    logger.info(f"Resetting GeoServer")
    r_url = GS_REST + 'reset'
    response = requests.post(r_url,
                             headers=headers_json,
                             auth=auth,
                             timeout=GS_REST_TIMEOUT,
                             )
    response.raise_for_status()
    logger.info(f"Resetting GeoServer done")


def reload(auth):
    logger.info(f"Reloading GeoServer")
    r_url = GS_REST + 'reload'
    response = requests.post(r_url,
                             headers=headers_json,
                             auth=auth,
                             timeout=4 * GS_REST_TIMEOUT,
                             )
    response.raise_for_status()
    logger.info(f"Reloading GeoServer done")


def get_square_bbox(bbox):
    # current_app.logger.info(f"bbox={bbox}")
    min_range = min(bbox[2] - bbox[0], bbox[3] - bbox[1]) / 2
    square_bbox = (
        (bbox[0] + bbox[2]) / 2 - min_range,
        (bbox[1] + bbox[3]) / 2 - min_range,
        (bbox[0] + bbox[2]) / 2 + min_range,
        (bbox[1] + bbox[3]) / 2 + min_range,
    )
    return square_bbox


def get_layer_thumbnail(wms_url, layername, bbox, crs, headers=None, wms_version='1.3.0', ):
    wms_bbox = crs_util.get_wms_bbox(crs, bbox, wms_version)
    response = requests.get(wms_url, params={
        'SERVICE': 'WMS',
        'REQUEST': 'GetMap',
        'VERSION': wms_version,
        'LAYERS': layername,
        'CRS': crs,
        'BBOX': ','.join([str(c) for c in wms_bbox]),
        'WIDTH': 300,
        'HEIGHT': 300,
        'FORMAT': 'image/png',
        'TRANSPARENT': 'TRUE',
    }, headers=headers, timeout=GS_REST_TIMEOUT,)
    return response


def get_feature_type(
        workspace, data_store, feature_type,
        gs_rest_workspaces=GS_REST_WORKSPACES):
    r_url = urljoin(gs_rest_workspaces,
                    f'{workspace}/datastores/{data_store}/featuretypes/{feature_type}')
    response = requests.get(r_url,
                            headers=headers_json,
                            auth=GS_AUTH,
                            timeout=GS_REST_TIMEOUT,
                            )
    response.raise_for_status()
    return response.json()['featureType']


def bbox_to_dict(bbox, crs):
    return {
        "minx": bbox[0],
        "miny": bbox[1],
        "maxx": bbox[2],
        "maxy": bbox[3],
        "crs": crs,
    }


def wms_direct(wms_url, xml=None, version=None, headers=None):
    version = version or WMS_VERSION
    try:
        wms = owslib_wms.WebMapService(wms_url, xml=xml.encode('utf-8') if xml is not None else xml, version=version, headers=headers)
    except requests.exceptions.HTTPError as exc:
        if exc.response.status_code == 404:
            return None
        raise exc
    except AttributeError as exc:
        if exc.args == ("'NoneType' object has no attribute 'find'",):
            return None
        raise exc
    return wms


def wfs_direct(wfs_url, xml=None, version=None, headers=None):
    version = version or WFS_VERSION
    try:
        wfs = owslib_wfs.WebFeatureService(wfs_url, xml=xml.encode('utf-8') if xml is not None else xml, version=version, headers=headers)
    except requests.exceptions.HTTPError as exc:
        if exc.response.status_code == 404:
            return None
        raise exc
    return wfs


def get_epsg_code(crs):
    authority, epsg_code = crs.split(':')
    assert authority == 'EPSG'
    return int(epsg_code)
