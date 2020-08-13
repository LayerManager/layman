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


def get_roles(auth):
    r_url = settings.LAYMAN_GS_REST_ROLES
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=auth
                     )
    r.raise_for_status()
    return r.json()['roleNames']


def ensure_role(role, auth):
    roles = get_roles(auth)
    role_exists = role in roles
    if not role_exists:
        app.logger.info(f"Role {role} does not exist yet, creating.")
        r = requests.post(
            urljoin(settings.LAYMAN_GS_REST_ROLES, 'role/' + role),
            headers=headers_json,
            auth=auth,
        )
        r.raise_for_status()
    else:
        app.logger.info(f"Role {role} already exists")
    role_created = not role_exists
    return role_created


def delete_role(role, auth):
    r = requests.delete(
        urljoin(settings.LAYMAN_GS_REST_ROLES, 'role/' + role),
        headers=headers_json,
        auth=auth,
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
                     auth=auth
                     )
    r.raise_for_status()
    # app.logger.info(f"users={r.text}")
    usernames = [u['userName'] for u in r.json()['users']]
    return usernames


def ensure_user(user, password, auth):
    usernames = get_usernames(auth)
    user_exists = user in usernames
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
            auth=auth,
        )
        r.raise_for_status()
    else:
        app.logger.info(f"User {user} already exists")
    user_created = not user_exists
    return user_created


def get_user_data_security_roles(username, type, auth):
    r = requests.get(
        settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS,
        headers=headers_json,
        auth=auth
    )
    r.raise_for_status()
    rules = r.json()
    try:
        rule = rules[username + '.*.' + type]
        roles = set(rule.split(','))
    except KeyError:
        roles = set()
    return roles


def ensure_user_data_security_roles(username, roles, type, auth):
    rule = username + '.*.' + type
    roles_str = ', '.join(roles)
    r = requests.post(
        settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS,
        data=json.dumps(
            {rule: roles_str}),
        headers=headers_json,
        auth=auth
    )
    r.raise_for_status()


def ensure_user_data_security(username, type, auth):
    roles = set(get_user_data_security_roles(username, type, auth))

    all_roles = authz.get_all_gs_roles(username, type)
    app.logger.info(f"username={username}, roles={roles}, all_roles={all_roles}")
    roles.difference_update(all_roles)

    authz_module = authz.get_authz_module()
    new_roles = authz_module.get_gs_roles(username, type)
    roles.update(new_roles)

    ensure_user_data_security_roles(username, roles, type, auth)


def get_all_workspaces(auth):
    key = FLASK_WORKSPACES_KEY
    if key not in g:
        r = requests.get(
            settings.LAYMAN_GS_REST_WORKSPACES,
            # data=json.dumps(payload),
            headers=headers_json,
            auth=auth
        )
        r.raise_for_status()
        if r.json()['workspaces'] == "":
            all_workspaces = []
        else:
            all_workspaces = r.json()['workspaces']['workspace']
        g.setdefault(key, all_workspaces)

    return g.get(key)


def get_layman_users(auth=settings.LAYMAN_GS_AUTH):
    usernames = get_usernames(auth)
    layman_users = set()
    for user in usernames:
        roles = get_user_roles(user, auth)
        if settings.LAYMAN_GS_ROLE in roles:
            layman_users.add(user)
    return layman_users


def ensure_user_db_store(username, auth):
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
        auth=auth
    )
    r.raise_for_status()


def delete_user_db_store(username, auth):
    r = requests.delete(
        urljoin(settings.LAYMAN_GS_REST_WORKSPACES, username + f'/datastores/{username}'),
        headers=headers_json,
        auth=auth
    )
    if r.status_code != 404:
        r.raise_for_status()


def ensure_user_workspace(username, auth):
    all_workspaces = get_all_workspaces(auth)
    if not any(ws['name'] == username for ws in all_workspaces):
        r = requests.post(
            settings.LAYMAN_GS_REST_WORKSPACES,
            data=json.dumps({'workspace': {'name': username}}),
            headers=headers_json,
            auth=auth
        )
        r.raise_for_status()

        ensure_user_data_security(username, 'r', auth)
        ensure_user_data_security(username, 'w', auth)
        ensure_user_db_store(username, auth)


def delete_user_workspace(username, auth):
    delete_user_db_store(username, auth)

    r = requests.delete(
        urljoin(settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS, username + '.*.r'),
        headers=headers_json,
        auth=auth
    )
    if r.status_code != 404:
        r.raise_for_status()

    r = requests.delete(
        urljoin(settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS, username + '.*.w'),
        headers=headers_json,
        auth=auth
    )
    if r.status_code != 404:
        r.raise_for_status()

    r = requests.delete(
        urljoin(settings.LAYMAN_GS_REST_WORKSPACES, username),
        headers=headers_json,
        auth=auth
    )
    if r.status_code != 404:
        r.raise_for_status()


def ensure_whole_user(username, auth=settings.LAYMAN_GS_AUTH):
    ensure_user(username, None, auth)
    role = username_to_rolename(username)
    ensure_role(role, auth)
    ensure_user_role(username, role, auth)
    ensure_user_role(username, settings.LAYMAN_GS_ROLE, auth)
    ensure_user_workspace(username, auth)


def delete_whole_user(username, auth=settings.LAYMAN_GS_AUTH):
    role = username_to_rolename(username)
    delete_user_workspace(username, auth)
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
    )
    user_not_exists = r.status_code == 404
    if not user_not_exists:
        r.raise_for_status()
    user_deleted = not user_not_exists
    return user_deleted


def get_user_roles(user, auth):
    r_url = urljoin(settings.LAYMAN_GS_REST_ROLES, f'user/{user}/')
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=auth
                     )
    r.raise_for_status()
    return r.json()['roleNames']


def ensure_user_role(user, role, auth):
    roles = get_user_roles(user, auth)
    association_exists = role in roles
    if not association_exists:
        app.logger.info(f"Role {role} not associated with user {user} yet, associating.")
        r_url = urljoin(settings.LAYMAN_GS_REST_ROLES, f'role/{role}/user/{user}/')
        r = requests.post(
            r_url,
            headers=headers_json,
            auth=auth,
        )
        r.raise_for_status()
    else:
        app.logger.info(f"Role {role} already associated with user {user}")
    association_created = not association_exists
    return association_created


def delete_user_role(user, role, auth):
    r_url = urljoin(settings.LAYMAN_GS_REST_ROLES, f'role/{role}/user/{user}/')
    r = requests.delete(
        r_url,
        headers=headers_json,
        auth=auth,
    )
    association_not_exists = r.status_code == 404
    if not association_not_exists:
        r.raise_for_status()
    association_deleted = not association_not_exists
    return association_deleted


def get_wms_settings(auth):
    r_url = settings.LAYMAN_GS_REST_WMS_SETTINGS
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=auth,
                     )
    r.raise_for_status()
    return r.json()['wms']


def get_wms_srs_list(auth, wms_settings=None):
    if wms_settings is None:
        wms_settings = get_wms_settings(auth)
    return wms_settings.get('srs', {}).get('string', [])


def ensure_wms_srs_list(srs_list, auth):
    wms_settings = get_wms_settings(auth)
    current_srs_list = get_wms_srs_list(auth, wms_settings=wms_settings)
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
            auth=auth,
        )
        r.raise_for_status()
    else:
        app.logger.info(f"Current SRS list {current_srs_list} already corresponds with requested one.")
    list_changed = not list_equals
    return list_changed


def get_global_settings(auth):
    r_url = settings.LAYMAN_GS_REST_SETTINGS
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=auth,
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
        app.logger.info(f"Current Proxy Base URL {current_url} not equals to requested {proxy_base_url}, changing.")
        r_url = settings.LAYMAN_GS_REST_SETTINGS
        r = requests.put(
            r_url,
            data=json.dumps({
                'global': global_settings
            }),
            headers=headers_json,
            auth=auth,
        )
        r.raise_for_status()
    else:
        app.logger.info(f"Current Proxy Base URL {current_url} already corresponds with requested one.")
    url_changed = not url_equals
    return url_changed


def get_roles_anyone(username):
    roles = {settings.LAYMAN_GS_ROLE, 'ROLE_ANONYMOUS', 'ROLE_AUTHENTICATED'}
    return roles


def get_roles_owner(username):
    roles = {username_to_rolename(username)}
    return roles
