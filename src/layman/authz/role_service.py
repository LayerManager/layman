from db import util as db_util
from layman import settings

ROLE_NAME_PATTERN = r'^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*$'
ROLE_SERVICE_SCHEMA = settings.LAYMAN_INTERNAL_ROLE_SERVICE_SCHEMA


def ensure_admin_roles():
    create_admin_roles_view = f"""CREATE OR REPLACE view {ROLE_SERVICE_SCHEMA}.admin_roles
    as
    select 'ADMIN' as name
    UNION ALL
    select 'GROUP_ADMIN'
    UNION ALL
    select %s
    ;"""
    db_util.run_statement(create_admin_roles_view, (settings.LAYMAN_GS_ROLE, ))

    create_admin_user_roles_view = f"""CREATE OR REPLACE view {ROLE_SERVICE_SCHEMA}.admin_user_roles
    as
    select %s as username, %s as rolename
    UNION ALL
    select %s, 'ADMIN'
    ;"""
    db_util.run_statement(create_admin_user_roles_view, (settings.LAYMAN_GS_USER, settings.LAYMAN_GS_ROLE, settings.LAYMAN_GS_USER))


def get_user_roles(username):
    query = f"""
select rolename from {ROLE_SERVICE_SCHEMA}.user_roles
where username = %s
  and rolename not in (%s, %s, %s)
  and LEFT(rolename, 5) != 'USER_'
  and rolename ~ %s
"""
    roles = db_util.run_query(query, (username, 'ADMIN', 'GROUP_ADMIN', settings.LAYMAN_GS_ROLE, ROLE_NAME_PATTERN))
    return {role[0] for role in roles}
