from . import util, users
from layman import settings

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
ROLE_EVERYONE = settings.RIGHTS_EVERYONE_ROLE


def get_publication_infos(username=None, pub_type=None):
    sql = f"""with const as (select %s username, %s pub_type)
select u.username,
       p.type,
       p.name,
       p.title,
       p.uuid,
       p.everyone_can_read,
       p.everyone_can_write,
       (select COALESCE(string_agg(u2.username, ', '), '')
        from {DB_SCHEMA}.rights r inner join
             {DB_SCHEMA}.users u2 on r.id_user = u2.id
        where r.id_publication = p.id
          and r.type = 'read') can_read_users,
       (select COALESCE(string_agg(u2.username, ', '), '')
        from {DB_SCHEMA}.rights r inner join
             {DB_SCHEMA}.users u2 on r.id_user = u2.id
        where r.id_publication = p.id
          and r.type = 'write') can_write_users
from const c inner join
     {DB_SCHEMA}.users u on (   u.username = c.username
                        or c.username is null) inner join
     {DB_SCHEMA}.publications p on p.id_user = u.id
                          and (   p.type = c.pub_type
                               or c.pub_type is null)
;"""
    values = util.run_query(sql, (username, pub_type,))
    infos = {layername: {'name': layername,
                         'title': title,
                         'uuid': uuid,
                         'type': type,
                         # 'can_read': set(),  # To be combination of everyone_can_read and can_read_users
                         # 'can_write': set(),  # To be combination of everyone_can_write and can_write_users
                         }
             for username, type, layername, title, uuid, everyone_can_read, everyone_can_write, can_read_users, can_write_users
             in values}
    return infos


def insert_publication(username, info):
    # TODO get_user_infos should be enough
    # user_id = users.get_user_infos(username)[username]["id"]
    user_id = users.ensure_user(username)
    insert_publications_sql = f'''insert into {DB_SCHEMA}.publications as p
        (id_user, name, title, type, uuid, everyone_can_read, everyone_can_write) values
        (%s, %s, %s, %s, %s, %s, %s)
returning id
;'''

    data = (user_id,
            info.get("name"),
            info.get("title"),
            info.get("publ_type_name"),
            info.get("uuid"),
            ROLE_EVERYONE in info.get("can_read"),
            ROLE_EVERYONE in info.get("can_write"),
            )
    pub_id = util.run_query(insert_publications_sql, data)
    return pub_id


def update_publication(username, info):
    user_id = users.get_user_infos(username)[username]["id"]
    insert_publications_sql = f'''update {DB_SCHEMA}.publications set
    title = coalesce(%s, title),
    everyone_can_read = coalesce(%s, everyone_can_read),
    everyone_can_write = coalesce(%s, everyone_can_write)
where id_user = %s
  and name = %s
  and type = %s
returning id
;'''

    data = (info.get("title"),
            ROLE_EVERYONE in (info.get("can_read") or set()),
            ROLE_EVERYONE in (info.get("can_write") or set()),
            user_id,
            info.get("name"),
            info.get("publ_type_name"),
            )
    pub_id = util.run_query(insert_publications_sql, data)
    return pub_id


def delete_publication(username, name, type):
    user_id = users.ensure_user(username)
    sql = f"""delete from {DB_SCHEMA}.publications p where p.id_user = %s and p.name = %s and p.type = %s;"""
    util.run_statement(sql, (user_id,
                             name,
                             type,))
