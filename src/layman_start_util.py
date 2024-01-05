import layman_settings as settings
from db import util as db_util
from geoserver import util as gs_util


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
    roles = db_util.run_query(query, (settings.ROLE_NAME_PATTERN,), uri_str=settings.LAYMAN_ROLE_SERVICE_URI)
    if roles:
        raise Exception(f"Roles not matching pattern '{settings.ROLE_NAME_PATTERN}' in JDBC Role service: {[role[0] for role in roles]}")

    not_expected_roles = [settings.RIGHTS_EVERYONE_ROLE, ] + gs_util.RESERVED_ROLE_NAMES
    query = f"""
    select name
    from {settings.LAYMAN_ROLE_SERVICE_SCHEMA}.roles
    where name = any(%s)
    """
    roles = db_util.run_query(query, (not_expected_roles,), uri_str=settings.LAYMAN_ROLE_SERVICE_URI)
    if roles:
        raise Exception(f"Roles {not_expected_roles} should not be in JDBC Role service.")

    query = f"""
    select name
    from {settings.LAYMAN_ROLE_SERVICE_SCHEMA}.roles
    where parent is not null
    """
    roles = db_util.run_query(query, uri_str=settings.LAYMAN_ROLE_SERVICE_URI)
    if roles:
        raise Exception(f"Roles in JDBC Role service should not have parent column filled: {[role[0] for role in roles]}.")


def validate_user_roles_table():
    exp_relation = [(settings.LAYMAN_GS_USER, 'ADMIN'),
                    (settings.LAYMAN_GS_USER, settings.LAYMAN_GS_ROLE),
                    (settings.GEOSERVER_ADMIN_USER, 'ADMIN'),
                    ]
    query = f"""
with exp_relations as(
SELECT w.name, %s
FROM {settings.LAYMAN_PRIME_SCHEMA}.users u inner join
     {settings.LAYMAN_PRIME_SCHEMA}.workspaces w on u.id_workspace = w.id
UNION ALL
select w.name as username,
       concat('USER_', UPPER(w.name)) as rolename
from {settings.LAYMAN_PRIME_SCHEMA}.users u inner join
     {settings.LAYMAN_PRIME_SCHEMA}.workspaces w on w.id = u.id_workspace
UNION ALL
select * from unnest (%s, %s) as exp_user_role(username, rolename)
)
select * from exp_relations
except
select username, rolename
from {settings.LAYMAN_ROLE_SERVICE_SCHEMA}.user_roles
    """
    user_roles = db_util.run_query(query, (settings.LAYMAN_GS_ROLE, [rel[0] for rel in exp_relation], [rel[1] for rel in exp_relation]), uri_str=settings.LAYMAN_ROLE_SERVICE_URI)
    if user_roles:
        raise Exception(
            f"Missing user-role relation in JDBC Role service table user_roles: {[{'username': user_role[0], 'rolename': user_role[1]} for user_role in user_roles]}")


def validate_role_service():
    validate_role_table()
    validate_user_roles_table()
