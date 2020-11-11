from . import util, workspaces
from layman import settings

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def ensure_user(id_workspace, userinfo):
    sql = f"""insert into {DB_SCHEMA}.users (id_workspace, given_name, family_name, middle_name, name, email, issuer_id, sub)
values (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (id_workspace) DO update SET id_workspace = EXCLUDED.id_workspace returning id;"""
    data = (id_workspace,
            userinfo["claims"]["given_name"],
            userinfo["claims"]["family_name"],
            userinfo["claims"]["middle_name"],
            userinfo["claims"]["name"],
            userinfo["claims"]["email"],
            userinfo["iss_id"],
            userinfo["sub"],
            )
    ids = util.run_query(sql, data)
    return ids[0][0]


def delete_user(username):
    sql = f"delete from {DB_SCHEMA}.users where id_workspace = (select w.id from {DB_SCHEMA}.workspaces w where w.name = %s);"
    util.run_statement(sql, (username,))
    workspaces.delete_workspace(username)


def get_user_infos(username=None):
    sql = f"""with const as (select %s username)
select u.id,
       w.name username,
       u.given_name,
       u.family_name,
       u.middle_name,
       u.name,
       u.email,
       u.issuer_id,
       u.sub
from {DB_SCHEMA}.workspaces w inner join
     {DB_SCHEMA}.users u on w.id = u.id_workspace inner join
     const c on (   c.username = w.name
                 or c.username is null)
order by w.name asc
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
