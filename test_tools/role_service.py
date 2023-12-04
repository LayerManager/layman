from db import util as db_util
from layman import settings


def ensure_role(rolename):
    insert_role_statement = f'''insert into {settings.LAYMAN_INTERNAL_ROLE_SERVICE_SCHEMA}.bussiness_roles(name) values (%s) ON CONFLICT (name) DO nothing;'''
    db_util.run_statement(insert_role_statement, (rolename,))


def delete_role(rolename):
    delete_statement = f"""delete from {settings.LAYMAN_INTERNAL_ROLE_SERVICE_SCHEMA}.bussiness_roles where name = %s;"""
    db_util.run_statement(delete_statement, (rolename,))


def ensure_user_role(username, rolename):
    ensure_role(rolename)
    insert_user_role_statement = f'''insert into {settings.LAYMAN_INTERNAL_ROLE_SERVICE_SCHEMA}.bussiness_user_roles(username, rolename) values (%s, %s) ON CONFLICT (username, rolename) DO nothing;'''
    db_util.run_statement(insert_user_role_statement, (username, rolename,))


def delete_user_role(username, rolename):
    delete_statement = f"""delete from {settings.LAYMAN_INTERNAL_ROLE_SERVICE_SCHEMA}.bussiness_user_roles where username = %s and rolename = %s;"""
    db_util.run_statement(delete_statement, (username, rolename,))
