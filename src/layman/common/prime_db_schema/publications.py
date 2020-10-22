from . import util, workspaces
from layman import settings, app

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
ROLE_EVERYONE = settings.RIGHTS_EVERYONE_ROLE


def get_publication_infos(username=None, pub_type=None):
    sql = f"""with const as (select %s username, %s pub_type)
select w.name as username,
       p.type,
       p.name,
       p.title,
       p.uuid,
       p.everyone_can_read,
       p.everyone_can_write,
       (select COALESCE(string_agg(w.name, ', '), '')
        from {DB_SCHEMA}.rights r inner join
             {DB_SCHEMA}.users u on r.id_user = u.id inner join
             {DB_SCHEMA}.workspaces w on w.id = u.id_workspace
        where r.id_publication = p.id
          and r.type = 'read') can_read_users,
       (select COALESCE(string_agg(w.name, ', '), '')
        from {DB_SCHEMA}.rights r inner join
             {DB_SCHEMA}.users u on r.id_user = u.id inner join
             {DB_SCHEMA}.workspaces w on w.id = u.id_workspace
        where r.id_publication = p.id
          and r.type = 'write') can_write_users
from const c inner join
     {DB_SCHEMA}.workspaces w on (   w.name = c.username
                                  or c.username is null) inner join
     {DB_SCHEMA}.publications p on p.id_workspace = w.id
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
    id_workspace = workspaces.ensure_workspace(username)
    insert_publications_sql = f'''insert into {DB_SCHEMA}.publications as p
        (id_workspace, name, title, type, uuid, everyone_can_read, everyone_can_write) values
        (%s, %s, %s, %s, %s, %s, %s)
returning id
;'''

    print(f'insert_publication username={username}, info={info}')
    data = (id_workspace,
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
    id_workspace = workspaces.get_workspace_infos(username)[username]["id"]
    insert_publications_sql = f'''update {DB_SCHEMA}.publications set
    title = coalesce(%s, title),
    everyone_can_read = coalesce(%s, everyone_can_read),
    everyone_can_write = coalesce(%s, everyone_can_write)
where id_workspace = %s
  and name = %s
  and type = %s
returning id
;'''

    data = (info.get("title"),
            ROLE_EVERYONE in (info.get("can_read") or set()),
            ROLE_EVERYONE in (info.get("can_write") or set()),
            id_workspace,
            info.get("name"),
            info.get("publ_type_name"),
            )
    pub_id = util.run_query(insert_publications_sql, data)
    return pub_id


def delete_publication(username, name, type):
    workspace_info = workspaces.get_workspace_infos(username).get(username)
    if workspace_info:
        id_workspace = workspace_info["id"]
        sql = f"""delete from {DB_SCHEMA}.publications p where p.id_workspace = %s and p.name = %s and p.type = %s;"""
        util.run_statement(sql, (id_workspace,
                                 name,
                                 type,))
    else:
        app.logger.warning(f'Deleting publication for NON existing workspace. workspace_name={username}, pub_name={name}, type={type}')
