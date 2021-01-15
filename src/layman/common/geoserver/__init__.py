import logging
import json
from functools import partial

import requests
import secrets
import string
from urllib.parse import urljoin
from layman import settings


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

WMS_SERVICE_TYPE = 'wms'
WFS_SERVICE_TYPE = 'wfs'

SERVICE_TYPES = [
    WMS_SERVICE_TYPE,
    WFS_SERVICE_TYPE,
]


def get_roles(auth):
    r_url = settings.LAYMAN_GS_REST_ROLES
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
            urljoin(settings.LAYMAN_GS_REST_ROLES, 'role/' + role),
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
        urljoin(settings.LAYMAN_GS_REST_ROLES, 'role/' + role),
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
    r_url = settings.LAYMAN_GS_REST_USERS
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
            settings.LAYMAN_GS_REST_USERS,
            # TODO https://osgeo-org.atlassian.net/browse/GEOS-8486
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
        settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS,
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
        urljoin(settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS, rule),
        data=json.dumps(
            {rule: roles_str}),
        headers=headers_json,
        auth=auth,
        timeout=5,
    )
    if r.status_code != 404:
        r.raise_for_status()

    r = requests.post(
        settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS,
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


def delete_security_roles(rule, auth):
    r = requests.delete(
        urljoin(settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS, rule),
        headers=headers_json,
        auth=auth,
        timeout=5,
    )
    if r.status_code != 404:
        r.raise_for_status()


def layman_users_to_geoserver_roles(layman_users):
    geoserver_roles = set()
    for layman_user in layman_users:
        if layman_user == settings.RIGHTS_EVERYONE_ROLE:
            geoserver_roles.add('ROLE_ANONYMOUS')
            geoserver_roles.add('ROLE_AUTHENTICATED')
        else:
            geoserver_roles.add(username_to_rolename(layman_user))
    return geoserver_roles


def get_all_workspaces(auth):
    r = requests.get(
        settings.LAYMAN_GS_REST_WORKSPACES,
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


def ensure_db_store(username, auth):
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
        auth=auth,
        timeout=5,
    )
    r.raise_for_status()


def delete_db_store(username, auth):
    r = requests.delete(
        urljoin(settings.LAYMAN_GS_REST_WORKSPACES, username + f'/datastores/{username}'),
        headers=headers_json,
        auth=auth,
        timeout=5,
    )
    if r.status_code != 404:
        r.raise_for_status()


def ensure_workspace(username, auth=settings.LAYMAN_GS_AUTH):
    all_workspaces = get_all_workspaces(auth)
    if username not in all_workspaces:
        r = requests.post(
            settings.LAYMAN_GS_REST_WORKSPACES,
            data=json.dumps({'workspace': {'name': username}}),
            headers=headers_json,
            auth=auth,
            timeout=5,
        )
        r.raise_for_status()
        ensure_db_store(username, auth)


def delete_workspace(username, auth=settings.LAYMAN_GS_AUTH):
    delete_db_store(username, auth)

    delete_security_roles(username + '.*.r', auth)
    delete_security_roles(username + '.*.w', auth)

    r = requests.delete(
        urljoin(settings.LAYMAN_GS_REST_WORKSPACES, username),
        headers=headers_json,
        auth=auth,
        timeout=5,
    )
    if r.status_code != 404:
        r.raise_for_status()


def ensure_whole_user(username, auth=settings.LAYMAN_GS_AUTH):
    ensure_user(username, None, auth)
    role = username_to_rolename(username)
    ensure_role(role, auth)
    ensure_user_role(username, role, auth)
    ensure_user_role(username, settings.LAYMAN_GS_ROLE, auth)
    ensure_workspace(username, auth)


def delete_whole_user(username, auth=settings.LAYMAN_GS_AUTH):
    role = username_to_rolename(username)
    delete_workspace(username, auth)
    delete_user_role(username, role, auth)
    delete_user_role(username, settings.LAYMAN_GS_ROLE, auth)
    delete_role(role, auth)
    delete_user(username, auth)


def username_to_rolename(username):
    return f"USER_{username.upper()}"


def delete_user(user, auth):
    r_url = urljoin(settings.LAYMAN_GS_REST_USER, user)
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
    r_url = urljoin(settings.LAYMAN_GS_REST_ROLES, f'user/{user}/')
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
        r_url = urljoin(settings.LAYMAN_GS_REST_ROLES, f'role/{role}/user/{user}/')
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
    r_url = urljoin(settings.LAYMAN_GS_REST_ROLES, f'role/{role}/user/{user}/')
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
        WMS_SERVICE_TYPE: settings.LAYMAN_GS_REST_WMS_SETTINGS,
        WFS_SERVICE_TYPE: settings.LAYMAN_GS_REST_WFS_SETTINGS,
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
        },
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
    r_url = settings.LAYMAN_GS_REST_SETTINGS
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
        r_url = settings.LAYMAN_GS_REST_SETTINGS
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
    r_url = settings.LAYMAN_GS_REST + 'reset'
    r = requests.post(r_url,
                      headers=headers_json,
                      auth=auth,
                      timeout=5,
                      )
    r.raise_for_status()
    logger.info(f"Resetting GeoServer done")


def reload(auth):
    logger.info(f"Reloading GeoServer")
    r_url = settings.LAYMAN_GS_REST + 'reload'
    r = requests.post(r_url,
                      headers=headers_json,
                      auth=auth,
                      timeout=20,
                      )
    r.raise_for_status()
    logger.info(f"Reloading GeoServer done")


def get_layer_square_bbox(owslib_wms, layername):
    bbox = list(next(t for t in owslib_wms[layername].crs_list if t[4].lower() == 'epsg:3857'))
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
