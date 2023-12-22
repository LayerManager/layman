import logging

from db import util as db_util
from geoserver import util as gs_util
from layman import settings

logger = logging.getLogger(__name__)

ROLE_NAME_PATTERN = r'^(?!.{65,})[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*$'


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
    roles = db_util.run_query(query, ('ADMIN', 'GROUP_ADMIN', settings.LAYMAN_GS_ROLE, ROLE_NAME_PATTERN), uri_str=settings.LAYMAN_ROLE_SERVICE_URI)
    return [role[0] for role in roles] + [settings.RIGHTS_EVERYONE_ROLE]


def validate_role_table():
    expected_roles = ['ADMIN', 'GROUP_ADMIN', settings.LAYMAN_GS_ROLE]
    query = f"""
    select unnest(%s)
    EXCEPT
    select name
    from {settings.LAYMAN_ROLE_SERVICE_SCHEMA}.roles
    """
    roles = db_util.run_query(query, (expected_roles,), uri_str=settings.LAYMAN_ROLE_SERVICE_URI)
    if roles:
        raise Exception(f"Missing roles in JDBC Role service: {[role[0] for role in roles]}")

    query = f"""
    select name
    from {settings.LAYMAN_ROLE_SERVICE_SCHEMA}.roles
    where name !~ %s
    """
    roles = db_util.run_query(query, (ROLE_NAME_PATTERN,), uri_str=settings.LAYMAN_ROLE_SERVICE_URI)
    if roles:
        raise Exception(f"Roles not matching pattern '{ROLE_NAME_PATTERN}' in JDBC Role service: {[role[0] for role in roles]}")

    query = f"""
    select name
    from {settings.LAYMAN_ROLE_SERVICE_SCHEMA}.roles
    where name = any(%s)
    """
    roles = db_util.run_query(query, ([settings.RIGHTS_EVERYONE_ROLE, ] + gs_util.RESERVED_ROLE_NAMES,), uri_str=settings.LAYMAN_ROLE_SERVICE_URI)
    if roles:
        raise Exception(f"Role '{settings.RIGHTS_EVERYONE_ROLE}' should not be in JDBC Role service.")

    query = f"""
    select name
    from {settings.LAYMAN_ROLE_SERVICE_SCHEMA}.roles
    where parent is not null
    """
    roles = db_util.run_query(query, uri_str=settings.LAYMAN_ROLE_SERVICE_URI)
    if roles:
        raise Exception(f"Roles in JDBC Role service should not have parent column filled: {[role[0] for role in roles]}.")


def validate_role_service():
    validate_role_table()
