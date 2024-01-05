import logging

from db import util as db_util
from layman import settings

logger = logging.getLogger(__name__)


def get_user_roles(username):
    query = f"""
select rolename from {settings.LAYMAN_ROLE_SERVICE_SCHEMA}.user_roles
where username = %s
  and rolename not in (%s, %s, %s)
  and LEFT(rolename, 5) != 'USER_'
  and rolename ~ %s
"""
    roles = db_util.run_query(query,
                              (username, 'ADMIN', 'GROUP_ADMIN', settings.LAYMAN_GS_ROLE, settings.ROLE_NAME_PATTERN),
                              uri_str=settings.LAYMAN_ROLE_SERVICE_URI)
    return {role[0] for role in roles}


def get_existent_roles(roles_to_check):
    query = f"""
select name from {settings.LAYMAN_ROLE_SERVICE_SCHEMA}.roles where name = ANY(%s)
    """
    rows = db_util.run_query(query, (list(roles_to_check),), uri_str=settings.LAYMAN_ROLE_SERVICE_URI)
    return {row[0] for row in rows}


def get_all_roles():
    query = f"""
    select name
    from {settings.LAYMAN_ROLE_SERVICE_SCHEMA}.roles
    where name not in (%s, %s, %s)
      and LEFT(name, 5) != 'USER_'
      and name ~ %s
    """
    roles = db_util.run_query(query, ('ADMIN', 'GROUP_ADMIN', settings.LAYMAN_GS_ROLE, settings.ROLE_NAME_PATTERN), uri_str=settings.LAYMAN_ROLE_SERVICE_URI)
    return [role[0] for role in roles] + [settings.RIGHTS_EVERYONE_ROLE]
