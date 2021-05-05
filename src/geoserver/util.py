import io
import logging
import json
from functools import partial
import xml.etree.ElementTree as ET
import secrets
import string
from urllib.parse import urljoin
import requests

from . import GS_REST_ROLES, GS_REST_USERS, GS_REST_SECURITY_ACL_LAYERS, GS_REST_WORKSPACES, GS_REST_STYLES, GS_AUTH,\
    GS_REST_WMS_SETTINGS, GS_REST_WFS_SETTINGS, GS_REST_USER, GS_REST_SETTINGS, GS_REST
from .error import Error


logger = logging.getLogger(__name__)

FLASK_RULES_KEY = f"{__name__}:RULES"

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

headers_sld = {
    'Accept': 'application/vnd.ogc.sld+xml',
    'Content-type': 'application/xml',
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
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=auth,
                     timeout=5,
                     )
    r.raise_for_status()
    return r.json()['roleNames']


def ensure_role(role, auth):
    roles = get_roles(auth)
    role_exists = role in roles
    if not role_exists:
        logger.info(f"Role {role} does not exist yet, creating.")
        r = requests.post(
            urljoin(GS_REST_ROLES, 'role/' + role),
            headers=headers_json,
            auth=auth,
            timeout=5,
        )
        r.raise_for_status()
    else:
        logger.info(f"Role {role} already exists")
    role_created = not role_exists
    return role_created


def delete_role(role, auth):
    r = requests.delete(
        urljoin(GS_REST_ROLES, 'role/' + role),
        headers=headers_json,
        auth=auth,
        timeout=5,
    )
    role_not_exists = r.status_code == 404
    if not role_not_exists:
        r.raise_for_status()
    role_deleted = not role_not_exists
    return role_deleted


def get_usernames(auth):
    r_url = GS_REST_USERS
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=auth,
                     timeout=5,
                     )
    r.raise_for_status()
    # logger.info(f"users={r.text}")
    usernames = [u['userName'] for u in r.json()['users']]
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
        r = requests.post(
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
            timeout=5,
        )
        r.raise_for_status()
    else:
        logger.info(f"User {user} already exists")
    user_created = not user_exists
    return user_created


def get_workspace_security_roles(workspace, type, auth):
    return get_security_roles(workspace + '.*.' + type, auth)


def get_security_roles(rule, auth):
    r = requests.get(
        GS_REST_SECURITY_ACL_LAYERS,
        headers=headers_json,
        auth=auth,
        timeout=5,
    )
    r.raise_for_status()
    rules = r.json()
    try:
        roles_string = rules[rule]
        roles = set(roles_string.split(','))
    except KeyError:
        roles = set()
    return roles


def ensure_security_roles(rule, roles, auth):
    roles_str = ', '.join(roles)

    logger.info(f"Ensure_security_roles rule={rule}, roles={roles}, roles_str={roles_str}")
    r = requests.delete(
        urljoin(GS_REST_SECURITY_ACL_LAYERS, rule),
        data=json.dumps(
            {rule: roles_str}),
        headers=headers_json,
        auth=auth,
        timeout=5,
    )
    if r.status_code != 404:
        r.raise_for_status()

    r = requests.post(
        GS_REST_SECURITY_ACL_LAYERS,
        data=json.dumps(
            {rule: roles_str}),
        headers=headers_json,
        auth=auth,
        timeout=5,
    )
    r.raise_for_status()


def ensure_workspace_security_roles(workspace, roles, type, auth):
    rule = workspace + '.*.' + type
    ensure_security_roles(rule, roles, auth)


def ensure_layer_security_roles(workspace, layername, roles, type, auth):
    rule = f"{workspace}.{layername}.{type}"
    ensure_security_roles(rule, roles, auth)


def delete_feature_type(geoserver_workspace, feature_type_name, auth):
    r = requests.delete(
        urljoin(GS_REST_WORKSPACES,
                geoserver_workspace + f'/datastores/{DEFAULT_DB_STORE_NAME}/featuretypes/' + feature_type_name),
        headers=headers_json,
        auth=auth,
        params={
            'recurse': 'true'
        },
        timeout=5,
    )
    if r.status_code != 404:
        r.raise_for_status()


def patch_feature_type(geoserver_workspace, feature_type_name, *, title=None, description=None, bbox=None, auth):
    ftype = dict()

    if title:
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
    if description:
        ftype['abstract'] = description
    if bbox:
        ftype['nativeBoundingBox'] = bbox

    ftype = {k: v for k, v in ftype.items() if v is not None}
    body = {
        "featureType": ftype
    }
    r = requests.put(
        urljoin(GS_REST_WORKSPACES,
                geoserver_workspace + '/datastores/postgresql/featuretypes/' + feature_type_name),
        data=json.dumps(body),
        headers=headers_json,
        auth=auth,
        timeout=5,
    )
    r.raise_for_status()


def delete_security_roles(rule, auth):
    r = requests.delete(
        urljoin(GS_REST_SECURITY_ACL_LAYERS, rule),
        headers=headers_json,
        auth=auth,
        timeout=5,
    )
    if r.status_code != 404:
        r.raise_for_status()


def get_all_workspaces(auth):
    r = requests.get(
        GS_REST_WORKSPACES,
        headers=headers_json,
        auth=auth,
        timeout=5,
    )
    r.raise_for_status()
    if r.json()['workspaces'] == "":
        all_workspaces = []
    else:
        all_workspaces = [workspace["name"] for workspace in r.json()['workspaces']['workspace']]

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
        r = requests.get(
            urljoin(GS_REST_STYLES, 'generic.sld'),
            auth=GS_AUTH,
            timeout=5,
        )
        r.raise_for_status()
        sld_file = io.BytesIO(r.content)
    r = requests.post(
        get_workspace_style_url(geoserver_workspace),
        data=json.dumps(
            {
                "style": {
                    "name": layername,
                    "format": "sld",
                    "filename": layername + ".sld"
                }
            }
        ),
        headers=headers_json,
        auth=GS_AUTH,
        timeout=5,
    )
    r.raise_for_status()

    tree = ET.parse(sld_file)
    root = tree.getroot()
    if 'version' in root.attrib and root.attrib['version'] == '1.1.0':
        sld_content_type = 'application/vnd.ogc.se+xml'
    else:
        sld_content_type = 'application/vnd.ogc.sld+xml'

    propertname_els = tree.findall('.//{http://www.opengis.net/ogc}PropertyName')
    if launder_function:
        for el in propertname_els:
            el.text = launder_function(el.text)

    sld_file = io.BytesIO()
    tree.write(
        sld_file,
        encoding=None,
        xml_declaration=True,
    )
    sld_file.seek(0)

    r = requests.put(
        get_workspace_style_url(geoserver_workspace, layername),
        data=sld_file.read(),
        headers={
            'Accept': 'application/json',
            'Content-type': sld_content_type,
        },
        auth=GS_AUTH,
        timeout=5,
    )
    if r.status_code == 400:
        raise Error(1, data=r.text)
    r.raise_for_status()
    r = requests.put(get_workspace_layer_url(geoserver_workspace, layername),
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
                     timeout=5,
                     )
    # app.logger.info(r.text)
    r.raise_for_status()


def get_workspace_style_response(geoserver_workspace, stylename, headers=None, auth=None):
    if headers is None:
        headers = headers_sld
    url = get_workspace_style_url(geoserver_workspace, stylename)
    r = requests.get(url,
                     auth=auth,
                     headers=headers,
                     timeout=5,
                     )
    return r


def delete_workspace_style(geoserver_workspace, stylename, auth=None):
    r = get_workspace_style_response(geoserver_workspace, stylename, auth=auth)
    if r.status_code == 404:
        return {}
    r.raise_for_status()
    sld_stream = io.BytesIO(r.content)

    style_url = get_workspace_style_url(geoserver_workspace, stylename)
    r = requests.delete(style_url,
                        headers=headers_json,
                        auth=GS_AUTH,
                        params={
                            'purge': 'true',
                            'recurse': 'true',
                        },
                        timeout=5,
                        )
    if r.status_code == 404:
        return {}
    r.raise_for_status()
    return sld_stream


def create_db_store(geoserver_workspace, auth, db_schema=None, pg_conn=None, ):
    db_schema = db_schema or geoserver_workspace
    r = requests.post(
        urljoin(GS_REST_WORKSPACES, geoserver_workspace + '/datastores'),
        data=json.dumps({
            "dataStore": {
                "name": DEFAULT_DB_STORE_NAME,
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
        timeout=5,
    )
    r.raise_for_status()


def delete_db_store(geoserver_workspace, auth):
    r = requests.delete(
        urljoin(GS_REST_WORKSPACES, geoserver_workspace + f'/datastores/{DEFAULT_DB_STORE_NAME}'),
        headers=headers_json,
        auth=auth,
        timeout=5,
    )
    if r.status_code != 404:
        r.raise_for_status()


def create_wms_store(geoserver_workspace, auth, wms_store_name, get_capabilities_url):
    r = requests.post(
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
        timeout=5,
    )
    r.raise_for_status()


def delete_wms_store(geoserver_workspace, auth, wms_store_name):
    url = urljoin(GS_REST_WORKSPACES, geoserver_workspace + f'/wmsstores/{wms_store_name}')
    r = requests.delete(
        url,
        headers=headers_json,
        auth=auth,
        timeout=5,
    )
    if r.status_code != 404:
        r.raise_for_status()


def delete_wms_layer(geoserver_workspace, layer, auth):
    url = urljoin(GS_REST_WORKSPACES, geoserver_workspace + f'/wmslayers/{layer}')
    r = requests.delete(
        url,
        headers=headers_json,
        auth=auth,
        timeout=5,
        params={
            'recurse': 'true'
        }
    )
    if r.status_code != 404:
        r.raise_for_status()


def patch_wms_layer(geoserver_workspace, layer, *, auth, bbox):
    wms_layer = {
        "enabled": True,
    }
    if bbox:
        wms_layer['nativeBoundingBox'] = bbox
        wms_layer['nativeCRS'] = 'EPSG:3857'
    r = requests.put(urljoin(GS_REST_WORKSPACES,
                             f'{geoserver_workspace}/wmslayers/{layer}'),
                     data=json.dumps({
                         "wmsLayer": wms_layer
                     }),
                     headers=headers_json,
                     auth=auth,
                     timeout=5,
                     )
    r.raise_for_status()


def ensure_workspace(geoserver_workspace, auth=None):
    auth = auth or GS_AUTH
    all_workspaces = get_all_workspaces(auth)
    if geoserver_workspace not in all_workspaces:
        r = requests.post(
            GS_REST_WORKSPACES,
            data=json.dumps({'workspace': {'name': geoserver_workspace}}),
            headers=headers_json,
            auth=auth,
            timeout=5,
        )
        r.raise_for_status()
        return True
    return False


def delete_workspace(geoserver_workspace, auth=None):
    auth = auth or GS_AUTH
    delete_security_roles(geoserver_workspace + '.*.r', auth)
    delete_security_roles(geoserver_workspace + '.*.w', auth)

    r = requests.delete(
        urljoin(GS_REST_WORKSPACES, geoserver_workspace),
        headers=headers_json,
        auth=auth,
        timeout=5,
    )
    if r.status_code != 404:
        r.raise_for_status()


def username_to_rolename(username):
    return f"USER_{username.upper()}"


def delete_user(user, auth):
    r_url = urljoin(GS_REST_USER, user)
    r = requests.delete(
        r_url,
        headers=headers_json,
        auth=auth,
        timeout=5,
    )
    user_not_exists = r.status_code == 404
    if not user_not_exists:
        r.raise_for_status()
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
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=auth,
                     timeout=5,
                     )
    r.raise_for_status()
    return r.json()['roleNames']


def ensure_user_role(user, role, auth):
    roles = get_user_roles(user, auth)
    association_exists = role in roles
    if not association_exists:
        logger.info(f"Role {role} not associated with user {user} yet, associating.")
        r_url = urljoin(GS_REST_ROLES, f'role/{role}/user/{user}/')
        r = requests.post(
            r_url,
            headers=headers_json,
            auth=auth,
            timeout=5,
        )
        r.raise_for_status()
    else:
        logger.info(f"Role {role} already associated with user {user}")
    association_created = not association_exists
    return association_created


def delete_user_role(user, role, auth):
    r_url = urljoin(GS_REST_ROLES, f'role/{role}/user/{user}/')
    r = requests.delete(
        r_url,
        headers=headers_json,
        auth=auth,
        timeout=5,
    )
    association_not_exists = r.status_code == 404
    if not association_not_exists:
        r.raise_for_status()
    association_deleted = not association_not_exists
    return association_deleted


def get_service_url(service):
    return {
        WMS_SERVICE_TYPE: GS_REST_WMS_SETTINGS,
        WFS_SERVICE_TYPE: GS_REST_WFS_SETTINGS,
    }[service]


def get_service_settings(service, auth):
    r_url = get_service_url(service)
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=auth,
                     timeout=5,
                     )
    r.raise_for_status()
    return r.json()[service]


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
        r = requests.put(
            r_url,
            data=json.dumps({
                service: service_settings,
            }),
            headers=headers_json,
            auth=auth,
            timeout=5,
        )
        r.raise_for_status()
    else:
        logger.info(f"Service {service}: Current SRS list {current_srs_list} already corresponds with requested one.")
    return list_change


ensure_wms_srs_list = partial(ensure_service_srs_list, WMS_SERVICE_TYPE)
ensure_wfs_srs_list = partial(ensure_service_srs_list, WFS_SERVICE_TYPE)


def get_global_settings(auth):
    r_url = GS_REST_SETTINGS
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=auth,
                     timeout=5,
                     )
    r.raise_for_status()
    return r.json()['global']


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
        r = requests.put(
            r_url,
            data=json.dumps({
                'global': global_settings
            }),
            headers=headers_json,
            auth=auth,
            timeout=5,
        )
        r.raise_for_status()
    else:
        logger.info(f"Current Proxy Base URL {current_url} already corresponds with requested one.")
    url_changed = not url_equals
    return url_changed


def reset(auth):
    logger.info(f"Resetting GeoServer")
    r_url = GS_REST + 'reset'
    r = requests.post(r_url,
                      headers=headers_json,
                      auth=auth,
                      timeout=5,
                      )
    r.raise_for_status()
    logger.info(f"Resetting GeoServer done")


def reload(auth):
    logger.info(f"Reloading GeoServer")
    r_url = GS_REST + 'reload'
    r = requests.post(r_url,
                      headers=headers_json,
                      auth=auth,
                      timeout=20,
                      )
    r.raise_for_status()
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


def get_layer_thumbnail(wms_url, layername, bbox, headers=None, wms_version='1.3.0'):
    r = requests.get(wms_url, params={
        'SERVICE': 'WMS',
        'REQUEST': 'GetMap',
        'VERSION': wms_version,
        'LAYERS': layername,
        'CRS': 'EPSG:3857',
        'BBOX': ','.join([str(c) for c in bbox]),
        'WIDTH': 300,
        'HEIGHT': 300,
        'FORMAT': 'image/png',
        'TRANSPARENT': 'TRUE',
    }, headers=headers, timeout=5,)
    return r


def get_feature_type(
        workspace, data_store, feature_type,
        gs_rest_workspaces=GS_REST_WORKSPACES):
    r_url = urljoin(gs_rest_workspaces,
                    f'{workspace}/datastores/{data_store}/featuretypes/{feature_type}')
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=GS_AUTH,
                     timeout=5,
                     )
    r.raise_for_status()
    return r.json()['featureType']


def bbox_to_native_bbox(bbox):
    return {
        "minx": bbox[0],
        "miny": bbox[1],
        "maxx": bbox[2],
        "maxy": bbox[3],
        "crs": "EPSG:3857",
    }
