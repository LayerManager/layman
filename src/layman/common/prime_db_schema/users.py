from . import util
from layman.http import LaymanError
from layman import settings

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def ensure_user(username):
    sql = f"""insert into {DB_SCHEMA}.users (username) values (%s)
ON CONFLICT (username) DO update SET username = EXCLUDED.username returning id;"""
    ids = util.run_query(sql, (username, ))
    return ids[0][0]


def delete_user(username):
    sql = f"delete from {DB_SCHEMA}.users where username = %s;"
    util.run_statement(sql, (username, ))


def get_user_infos(username=None):
    sql = f"""with const as (select %s username)
select u.id, u.username
from {DB_SCHEMA}.users u inner join
     const c on (   c.username = u.username
                 or c.username is null)
;"""
    values = util.run_query(sql, (username, ))
    result = {username: {"id": user_id,
                         "username": username} for user_id, username in values}
    return result


def get_usernames():
    return get_user_infos().keys()


def check_username(username, conn_cur=None):
    if username in settings.PG_NON_USER_SCHEMAS:
        raise LaymanError(35, {'reserved_by': __name__, 'schema': username})
