from . import util
from layman import settings

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def ensure_user(username, userinfo=None):
    sql = f"""insert into {DB_SCHEMA}.users (username, given_name, family_name, middle_name, name, email, issuer_id, sub)
values (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (username) DO update SET username = EXCLUDED.username returning id;"""
    if userinfo:
        data = (username,
                userinfo["claims"]["given_name"],
                userinfo["claims"]["family_name"],
                userinfo["claims"]["middle_name"],
                userinfo["claims"]["name"],
                userinfo["claims"]["email"],
                userinfo["iss_id"],
                userinfo["sub"],
                )
    else:
        data = (username,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                )
    ids = util.run_query(sql, data)
    return ids[0][0]


def delete_user(username):
    sql = f"delete from {DB_SCHEMA}.users where username = %s;"
    util.run_statement(sql, (username,))


def get_user_infos(username=None):
    sql = f"""with const as (select %s username)
select u.id,
       u.username,
       u.given_name,
       u.family_name,
       u.middle_name,
       u.name,
       u.email,
       u.issuer_id,
       u.sub
from {DB_SCHEMA}.users u inner join
     const c on (   c.username = u.username
                 or c.username is null)
order by u.username asc
;"""
    values = util.run_query(sql, (username,))
    result = {username: {"id": user_id,
                         "username": username,
                         "given_name": given_name,
                         "family_name": family_name,
                         "middle_name": middle_name,
                         "name": name,
                         "email": email,
                         "issuer_id": issuer_id,
                         "sub": sub,
                         } for user_id, username, given_name, family_name, middle_name, name, email, issuer_id, sub in values}
    return result


def get_usernames():
    return get_user_infos().keys()


def check_username(username, conn_cur=None):
    pass
