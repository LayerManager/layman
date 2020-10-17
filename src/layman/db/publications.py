from . import utils, users
from layman import settings
from flask import current_app as app

DB_SCHEMA = settings.PG_LAYMAN_SCHEMA


def get_publication_infos(username=None, pub_type=None):
    sql = f"""with const as (select %s username, %s pub_type)
select u.username,
       p.type,
       p.name,
       p.title,
       p.uuid,
       p.everyone_can_read,
       p.everyone_can_write,
       (select string_agg(u2.username, ', ')
        from {DB_SCHEMA}.rights r inner join
             {DB_SCHEMA}.users u2 on r.id_user = u2.id
        where r.id_publication = p.id
          and r.type = 'read') can_read_users,
       (select string_agg(u2.username, ', ')
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
    values = utils.run_query(sql, (username, pub_type,))
    infos = {layername: {'name': layername,
                         'title': title,
                         'uuid': uuid,
                         'type': type,
                         'everyone_can_read': everyone_can_read,
                         'everyone_can_write': everyone_can_write,
                         'can_read_users': can_read_users,
                         'can_write_users': can_write_users,
                         }
             for username, type, layername, title, uuid, everyone_can_read, everyone_can_write, can_read_users, can_write_users
             in values}
    return infos


def insert_publication(username, info):
    user_id = users.ensure_user(username)
    insert_publications_sql = f'''insert into {DB_SCHEMA}.publications as p
        (id_user, name, title, type, uuid, everyone_can_read, everyone_can_write) values
        (%s, %s, %s, %s, coalesce(%s, 'this should never appear!'), coalesce(%s, False), coalesce(%s, False))
returning id
;'''

    data = (user_id,
            info.get("name"),
            info.get("title"),
            info.get("publ_type_name"),
            info.get("uuid"),
            info.get("everyone_can_read"),
            info.get("everyone_can_write"),
            )
    pub_id = utils.run_query(insert_publications_sql, data)
    return pub_id


def update_publication(username, info):
    user_id = users.ensure_user(username)
    insert_publications_sql = f'''update layman.publications set
    title = %s,
    everyone_can_read = coalesce(%s, everyone_can_read),
    everyone_can_write = coalesce(%s, everyone_can_write)
where id_user = %s
  and name = %s
  and type = %s
returning id
;'''

    data = (info.get("title"),
            info.get("everyone_can_read"),
            info.get("everyone_can_write"),
            user_id,
            info.get("name"),
            info.get("publ_type_name"),
            )
    pub_id = utils.run_query(insert_publications_sql, data)
    return pub_id


def delete_publication(username, name, type):
    user_id = users.ensure_user(username)
    sql = f"""delete from {DB_SCHEMA}.publications p where p.id_user = %s and p.name = %s and p.type = %s;"""
    utils.run_statement(sql, (user_id,
                              name,
                              type,))
