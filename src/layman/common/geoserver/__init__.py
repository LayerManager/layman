import json
import requests
from urllib.parse import urljoin
from flask import current_app as app
from layman import settings


headers_json = {
    'Accept': 'application/json',
    'Content-type': 'application/json',
}


def get_roles():
    r_url = settings.LAYMAN_GS_REST_ROLES
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=settings.GEOSERVER_ADMIN_AUTH
                     )
    r.raise_for_status()
    # return r.json()['roles']
    return r.json()['roleNames']


def ensure_role(role):
    roles = get_roles()
    role_exists = role in roles
    if not role_exists:
        app.logger.info(f"Role {role} does not exist yet, creating.")
        r = requests.post(
            urljoin(settings.LAYMAN_GS_REST_ROLES, 'role/' + role),
            headers=headers_json,
            auth=settings.GEOSERVER_ADMIN_AUTH,
        )
        r.raise_for_status()
    else:
        app.logger.info(f"Role {role} already exists")
    role_created = not role_exists
    return role_created


def delete_role(role):
    r = requests.delete(
        urljoin(settings.LAYMAN_GS_REST_ROLES, 'role/' + role),
        headers=headers_json,
        auth=settings.GEOSERVER_ADMIN_AUTH,
    )
    role_not_exists = r.status_code == 404
    if not role_not_exists:
        r.raise_for_status()
    role_deleted = not role_not_exists
    return role_deleted


def get_users():
    r_url = settings.LAYMAN_GS_REST_USERS
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=settings.GEOSERVER_ADMIN_AUTH
                     )
    r.raise_for_status()
    # app.logger.info(f"users={r.text}")
    return r.json()['users']


def ensure_user(user, password):
    users = get_users()
    user_exists = next((u for u in users if u['userName'] == user), None) is not None
    if not user_exists:
        app.logger.info(f"User {user} does not exist yet, creating.")
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
            auth=settings.GEOSERVER_ADMIN_AUTH,
        )
        r.raise_for_status()
    else:
        app.logger.info(f"User {user} already exists")
    user_created = not user_exists
    return user_created


def delete_user(user):
    r_url = urljoin(settings.LAYMAN_GS_REST_USER, user)
    r = requests.delete(
        r_url,
        headers=headers_json,
        auth=settings.GEOSERVER_ADMIN_AUTH,
    )
    user_not_exists = r.status_code == 404
    if not user_not_exists:
        r.raise_for_status()
    user_deleted = not user_not_exists
    return user_deleted


def get_user_roles(user):
    r_url = urljoin(settings.LAYMAN_GS_REST_ROLES, f'user/{user}/')
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=settings.GEOSERVER_ADMIN_AUTH
                     )
    r.raise_for_status()
    # return r.json()['roles']
    return r.json()['roleNames']


def ensure_user_role(user, role):
    roles = get_user_roles(user)
    association_exists = role in roles
    if not association_exists:
        app.logger.info(f"Role {role} not associated with user {user} yet, associating.")
        r_url = urljoin(settings.LAYMAN_GS_REST_ROLES, f'role/{role}/user/{user}/')
        r = requests.post(
            r_url,
            headers=headers_json,
            auth=settings.GEOSERVER_ADMIN_AUTH,
        )
        r.raise_for_status()
    else:
        app.logger.info(f"Role {role} already associated with user {user}")
    association_created = not association_exists
    return association_created


def delete_user_role(user, role):
    r_url = urljoin(settings.LAYMAN_GS_REST_ROLES, f'role/{role}/user/{user}/')
    r = requests.delete(
        r_url,
        headers=headers_json,
        auth=settings.GEOSERVER_ADMIN_AUTH,
    )
    association_not_exists = r.status_code == 404
    if not association_not_exists:
        r.raise_for_status()
    association_deleted = not association_not_exists
    return association_deleted


def get_wms_settings():
    r_url = settings.LAYMAN_GS_REST_WMS_SETTINGS
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=settings.LAYMAN_GS_AUTH,
                     )
    r.raise_for_status()
    return r.json()['wms']


def get_wms_srs_list(wms_settings=None):
    if wms_settings is None:
        wms_settings = get_wms_settings()
    return wms_settings.get('srs', {}).get('string', [])


def ensure_wms_srs_list(srs_list):
    wms_settings = get_wms_settings()
    current_srs_list = get_wms_srs_list(wms_settings=wms_settings)
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
            auth=settings.LAYMAN_GS_AUTH,
        )
        r.raise_for_status()
    else:
        app.logger.info(f"Current SRS list {current_srs_list} already corresponds with requested one.")
    list_changed = not list_equals
    return list_changed


def get_global_settings():
    r_url = settings.LAYMAN_GS_REST_SETTINGS
    r = requests.get(r_url,
                     headers=headers_json,
                     auth=settings.LAYMAN_GS_AUTH,
                     )
    r.raise_for_status()
    return r.json()['global']


def get_proxy_base_url(global_settings=None):
    if global_settings is None:
        global_settings = get_global_settings()
    return global_settings['settings'].get('proxyBaseUrl', None)


def ensure_proxy_base_url(proxy_base_url):
    global_settings = get_global_settings()
    current_url = get_proxy_base_url(global_settings=global_settings)
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
            auth=settings.LAYMAN_GS_AUTH,
        )
        r.raise_for_status()
    else:
        app.logger.info(f"Current Proxy Base URL {current_url} already corresponds with requested one.")
    url_changed = not url_equals
    return url_changed
