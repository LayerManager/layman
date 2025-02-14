from db import util as db_util
from layman import settings


def delete_user_roles(username):
    delete_statement = f"""delete from {settings.LAYMAN_INTERNAL_ROLE_SERVICE_SCHEMA}.bussiness_user_roles where username = %s;"""
    db_util.run_statement(delete_statement, (username,))
