import json
import requests
import secrets
import string
from urllib.parse import urljoin
from flask import g, current_app as app
from layman import settings
from layman import util as layman_util
from layman.authz import util as authz


FLASK_WORKSPACES_KEY = f"{__name__}:WORKSPACES"
FLASK_RULES_KEY = f"{__name__}:RULES"

headers_json = {
    'Accept': 'application/json',
    'Content-type': 'application/json',
}


def get_roles(authz_type):
    r_url = settings.LAYMAN_GS_REST_ROLES
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=authz_type
                     )
    r.raise_for_status()
    return r.json()['roleNames']


def ensure_role(role, authz_type):
    roles = get_roles(authz_type)
    role_exists = role in roles
    if not role_exists:
        app.logger.info(f"Role {role} does not exist yet, creating.")
        r = requests.post(
            urljoin(settings.LAYMAN_GS_REST_ROLES, 'role/' + role),
            headers=headers_json,
            auth=authz_type,
        )
        r.raise_for_status()
    else:
        app.logger.info(f"Role {role} already exists")
    role_created = not role_exists
    return role_created


def delete_role(role, authz_type):
    r = requests.delete(
        urljoin(settings.LAYMAN_GS_REST_ROLES, 'role/' + role),
        headers=headers_json,
        auth=authz_type,
    )
    role_not_exists = r.status_code == 404
    if not role_not_exists:
        r.raise_for_status()
    role_deleted = not role_not_exists
    return role_deleted


def get_users(authz_type):
    r_url = settings.LAYMAN_GS_REST_USERS
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=authz_type
                     )
    r.raise_for_status()
    # app.logger.info(f"users={r.text}")
    return r.json()['users']


def ensure_user(user, password, authz_type):
    users = get_users(authz_type)
    user_exists = next((u for u in users if u['userName'] == user), None) is not None
    if not user_exists:
        app.logger.info(f"User {user} does not exist yet, creating.")
        if password is None:
            # generate random password
            # https://stackoverflow.com/a/23728630
            password = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(32))
            # we usually don't want to log passwords
            # app.logger.info(f"User {user}'s automatically generated password is {password}")
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
            auth=authz_type,
        )
        r.raise_for_status()
    else:
        app.logger.info(f"User {user} already exists")
    user_created = not user_exists
    return user_created


def get_user_data_security_roles(username, type, authz_type):
    r = requests.get(
        settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS,
        headers=headers_json,
        auth=authz_type
    )
    r.raise_for_status()
    rules = r.json()
    try:
        rule = rules[username + '.*.' + type]
        roles = set(rule.split(','))
    except KeyError:
        roles = set()
    return roles


def ensure_user_data_security_roles(username, roles, type, authz_type):
    rule = username + '.*.' + type
    roles_str = ', '.join(roles)
    r = requests.post(
        settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS,
        data=json.dumps(
            {rule: roles_str}),
        headers=headers_json,
        auth=authz_type
    )
    r.raise_for_status()


def ensure_user_data_security(username, type, authz_type):
    roles = get_user_data_security_roles(username, type, authz_type)

    all_roles = authz.get_all_GS_roles(username, type)
    roles.difference_update(all_roles)

    authz_module = authz.get_authz_module()
    new_roles = authz_module.get_GS_roles(username, type)
    roles.update(new_roles)

    ensure_user_data_security_roles(username, roles, type, authz_type)


def get_all_workspaces(authz_type):
    key = FLASK_WORKSPACES_KEY
    if key not in g:
        r = requests.get(
            settings.LAYMAN_GS_REST_WORKSPACES,
            # data=json.dumps(payload),
            headers=headers_json,
            auth=authz_type
        )
        r.raise_for_status()
        if r.json()['workspaces'] == "":
            all_workspaces = []
        else:
            all_workspaces = r.json()['workspaces']['workspace']
        g.setdefault(key, all_workspaces)

    return g.get(key)


def get_layman_users(authz_type=settings.LAYMAN_GS_AUTH):
    users = get_users(authz_type)
    layman_users = set()
    for user in users:
        roles = get_user_roles(user, authz_type)
        if settings.LAYMAN_GS_ROLE in roles:
            layman_users.add(user)
    return layman_users


def ensure_user_db_store(username, authz_type):
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
        auth=authz_type
    )
    r.raise_for_status()


def delete_user_db_store(username, authz_type):
    r = requests.delete(
        urljoin(settings.LAYMAN_GS_REST_WORKSPACES, username + f'/datastores/{username}'),
        headers=headers_json,
        auth=authz_type
    )
    if r.status_code != 404:
        r.raise_for_status()


def ensure_user_workspace(username, authz_type):
    all_workspaces = get_all_workspaces(authz_type)
    if not any(ws['name'] == username for ws in all_workspaces):
        r = requests.post(
            settings.LAYMAN_GS_REST_WORKSPACES,
            data=json.dumps({'workspace': {'name': username}}),
            headers=headers_json,
            auth=authz_type
        )
        r.raise_for_status()

        ensure_user_data_security(username, 'r', authz_type)
        ensure_user_data_security(username, 'w', authz_type)
        ensure_user_db_store(username, authz_type)


def delete_user_workspace(username, authz_type):
    delete_user_db_store(username, authz_type)

    r = requests.delete(
        urljoin(settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS, username + '.*.r'),
        headers=headers_json,
        auth=authz_type
    )
    if r.status_code != 404:
        r.raise_for_status()

    r = requests.delete(
        urljoin(settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS, username + '.*.w'),
        headers=headers_json,
        auth=authz_type
    )
    if r.status_code != 404:
        r.raise_for_status()

    r = requests.delete(
        urljoin(settings.LAYMAN_GS_REST_WORKSPACES, username),
        headers=headers_json,
        auth=authz_type
    )
    if r.status_code != 404:
        r.raise_for_status()


def ensure_whole_user(username, authz_type=settings.LAYMAN_GS_AUTH):
    ensure_user(username, None, authz_type)
    role = username_to_rolename(username)
    ensure_role(role, authz_type)
    ensure_user_role(username, role, authz_type)
    ensure_user_role(username, settings.LAYMAN_GS_ROLE, authz_type)
    ensure_user_workspace(username, authz_type)


def delete_whole_user(username, authz_type=settings.LAYMAN_GS_AUTH):
    role = username_to_rolename(username)
    delete_user_workspace(username, authz_type)
    delete_user_role(username, role, authz_type)
    delete_user_role(username, settings.LAYMAN_GS_ROLE, authz_type)
    delete_role(role, authz_type)
    delete_user(username, authz_type)


def username_to_rolename(username):
    return f"USER_{username.upper()}"


def delete_user(user, authz_type):
    r_url = urljoin(settings.LAYMAN_GS_REST_USER, user)
    r = requests.delete(
        r_url,
        headers=headers_json,
        auth=authz_type,
    )
    user_not_exists = r.status_code == 404
    if not user_not_exists:
        r.raise_for_status()
    user_deleted = not user_not_exists
    return user_deleted


def get_user_roles(user, authz_type):
    r_url = urljoin(settings.LAYMAN_GS_REST_ROLES, f'user/{user}/')
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=authz_type
                     )
    r.raise_for_status()
    return r.json()['roleNames']


def ensure_user_role(user, role, authz_type):
    roles = get_user_roles(user, authz_type)
    association_exists = role in roles
    if not association_exists:
        app.logger.info(f"Role {role} not associated with user {user} yet, associating.")
        r_url = urljoin(settings.LAYMAN_GS_REST_ROLES, f'role/{role}/user/{user}/')
        r = requests.post(
            r_url,
            headers=headers_json,
            auth=authz_type,
        )
        r.raise_for_status()
    else:
        app.logger.info(f"Role {role} already associated with user {user}")
    association_created = not association_exists
    return association_created


def delete_user_role(user, role, authz_type):
    r_url = urljoin(settings.LAYMAN_GS_REST_ROLES, f'role/{role}/user/{user}/')
    r = requests.delete(
        r_url,
        headers=headers_json,
        auth=authz_type,
    )
    association_not_exists = r.status_code == 404
    if not association_not_exists:
        r.raise_for_status()
    association_deleted = not association_not_exists
    return association_deleted


def get_wms_settings(authz_type):
    r_url = settings.LAYMAN_GS_REST_WMS_SETTINGS
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=authz_type,
                     )
    r.raise_for_status()
    return r.json()['wms']


def get_wms_srs_list(authz_type, wms_settings=None):
    if wms_settings is None:
        wms_settings = get_wms_settings(authz_type)
    return wms_settings.get('srs', {}).get('string', [])


def ensure_wms_srs_list(srs_list, authz_type):
    wms_settings = get_wms_settings(authz_type)
    current_srs_list = get_wms_srs_list(authz_type, wms_settings=wms_settings)
    list_equals = set(current_srs_list) == set(srs_list)
    if not list_equals:
        wms_settings['srs'] = {
            'string': srs_list,
        },
        app.logger.info(f"Current SRS list {current_srs_list} not equals to requested {srs_list}, changing.")
        r_url = settings.LAYMAN_GS_REST_WMS_SETTINGS
        r = requests.put(
            r_url,
            data=json.dumps({
                'wms': wms_settings,
            }),
            headers=headers_json,
            auth=authz_type,
        )
        r.raise_for_status()
    else:
        app.logger.info(f"Current SRS list {current_srs_list} already corresponds with requested one.")
    list_changed = not list_equals
    return list_changed


def get_global_settings(authz_type):
    r_url = settings.LAYMAN_GS_REST_SETTINGS
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=authz_type,
                     )
    r.raise_for_status()
    return r.json()['global']


def get_proxy_base_url(authz_type, global_settings=None):
    if global_settings is None:
        global_settings = get_global_settings(authz_type)
    return global_settings['settings'].get('proxyBaseUrl', None)


def ensure_proxy_base_url(proxy_base_url, authz_type):
    global_settings = get_global_settings(authz_type)
    current_url = get_proxy_base_url(authz_type, global_settings=global_settings)
    url_equals = proxy_base_url == current_url
    if not url_equals:
        global_settings['settings']['proxyBaseUrl'] = proxy_base_url
        app.logger.info(f"Current Proxy Base URL {current_url} not equals to requested {proxy_base_url}, changing.")
        r_url = settings.LAYMAN_GS_REST_SETTINGS
        r = requests.put(
            r_url,
            data=json.dumps({
                'global': global_settings
            }),
            headers=headers_json,
            auth=authz_type,
        )
        r.raise_for_status()
    else:
        app.logger.info(f"Current Proxy Base URL {current_url} already corresponds with requested one.")
    url_changed = not url_equals
    return url_changed


def get_roles_anyone(username):
    roles = {'ADMIN', settings.LAYMAN_GS_ROLE, 'ROLE_ANONYMOUS', 'ROLE_AUTHENTICATED'}
    return roles


def get_roles_owner(username):
    roles = {'ADMIN', username_to_rolename(username)}
    return roles
