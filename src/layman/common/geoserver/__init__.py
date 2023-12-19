from geoserver.util import username_to_rolename
from layman import settings
from layman.authz import is_user


def layman_users_and_roles_to_geoserver_roles(layman_users_and_roles):
    geoserver_roles = set()
    for layman_user in layman_users_and_roles:
        if layman_user == settings.RIGHTS_EVERYONE_ROLE:
            geoserver_roles.add('ROLE_ANONYMOUS')
            geoserver_roles.add('ROLE_AUTHENTICATED')
        elif is_user(layman_user):
            geoserver_roles.add(username_to_rolename(layman_user))
        else:
            geoserver_roles.add(layman_user)
    return geoserver_roles
