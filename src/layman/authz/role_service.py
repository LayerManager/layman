from db import util as db_util
from layman import settings

ROLE_NAME_PATTERN = r'^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*$'


def get_user_roles(username):
    query = f"""
select rolename from {settings.LAYMAN_ROLE_SERVICE_SCHEMA}.user_roles
where username = %s
  and rolename not in (%s, %s, %s)
  and LEFT(rolename, 5) != 'USER_'
  and rolename ~ %s
"""
    roles = db_util.run_query(query, (username, 'ADMIN', 'GROUP_ADMIN', settings.LAYMAN_GS_ROLE, ROLE_NAME_PATTERN), uri_str=settings.LAYMAN_ROLE_SERVICE_URI)
    return {role[0] for role in roles}
