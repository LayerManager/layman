from geoserver.util import username_to_rolename
from layman import settings


def layman_users_to_geoserver_roles(layman_users):
    geoserver_roles = set()
    for layman_user in layman_users:
        if layman_user == settings.RIGHTS_EVERYONE_ROLE:
            geoserver_roles.add('ROLE_ANONYMOUS')
            geoserver_roles.add('ROLE_AUTHENTICATED')
        else:
            geoserver_roles.add(username_to_rolename(layman_user))
    return geoserver_roles
