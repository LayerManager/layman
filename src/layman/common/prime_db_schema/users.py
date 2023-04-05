from db import util as db_util
from layman import settings
from . import workspaces

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


def ensure_user(id_workspace, userinfo):
    users = get_user_infos(id_workspace=id_workspace)
    if users:
        result = list(users.values())[0]["id"]
    else:
        sql = f"""insert into {DB_SCHEMA}.users (id_workspace, preferred_username, given_name, family_name, middle_name, name, email, issuer_id, sub)
    values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (id_workspace) DO update SET id_workspace = EXCLUDED.id_workspace returning id;"""
        data = (id_workspace,
                userinfo["claims"]["preferred_username"],
                userinfo["claims"]["given_name"],
                userinfo["claims"]["family_name"],
                userinfo["claims"]["middle_name"],
                userinfo["claims"]["name"],
                userinfo["claims"]["email"],
                userinfo["issuer_id"],
                userinfo["sub"],
                )
        ids = db_util.run_query(sql, data)
        result = ids[0][0]
    return result


def delete_user(username):
    sql = f"delete from {DB_SCHEMA}.users where id_workspace = (select w.id from {DB_SCHEMA}.workspaces w where w.name = %s);"
    deleted = db_util.run_statement(sql, (username,))
    if deleted:
        workspaces.delete_workspace(username)


def get_user_infos(username=None,
                   iss_sub=None,
                   id_workspace=None):
    assert not (username and iss_sub)
    iss_sub = iss_sub or {}

    join_clause = '1 = 1'
    if username:
        join_clause = 'c.username = w.name'
    elif iss_sub:
        join_clause = 'c.issuer_id = u.issuer_id and c.sub = u.sub'
    elif id_workspace:
        join_clause = 'c.id_workspace = w.id'

    sql = f"""with const as (select %s username, %s issuer_id, %s sub, %s id_workspace)
select u.id,
       w.name username,
       u.preferred_username,
       u.given_name,
       u.family_name,
       u.middle_name,
       u.name,
       u.email,
       u.issuer_id,
       u.sub
from {DB_SCHEMA}.workspaces w inner join
     {DB_SCHEMA}.users u on w.id = u.id_workspace inner join
     const c on (""" + join_clause + """)
order by w.name asc
;"""
    params = (username, iss_sub.get('issuer_id'), iss_sub.get('sub'), id_workspace)
    values = db_util.run_query(sql, params)
    result = {username: {"id": user_id,
                         "username": username,
                         "preferred_username": preferred_username,
                         "given_name": given_name,
                         "family_name": family_name,
                         "middle_name": middle_name,
                         "name": name,
                         "email": email,
                         "issuer_id": issuer_id,
                         "sub": sub,
                         } for user_id, username, preferred_username, given_name, family_name, middle_name, name, email, issuer_id, sub in values}
    return result


def get_usernames():
    return get_user_infos().keys()
