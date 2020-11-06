import logging
import psycopg2.extras

from . import util, workspaces
from layman import settings

logger = logging.getLogger(__name__)

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
ROLE_EVERYONE = settings.RIGHTS_EVERYONE_ROLE
psycopg2.extras.register_uuid()


def get_publication_infos(workspace_name=None, pub_type=None):
    sql = f"""with const as (select %s workspace_name, %s pub_type, %s everyone_role)
select p.id as id_publication,
       w.name as workspace_name,
       p.type,
       p.name,
       p.title,
       p.uuid::text,
       (select rtrim(concat(case when u.id is not null then w.name || ',' end,
                            string_agg(w2.name, ',') || ',',
                            case when p.everyone_can_read then c.everyone_role || ',' end
                            ), ',')
        from {DB_SCHEMA}.rights r inner join
             {DB_SCHEMA}.users u2 on r.id_user = u2.id inner join
             {DB_SCHEMA}.workspaces w2 on w2.id = u2.id_workspace
        where r.id_publication = p.id
          and r.type = 'read') can_read_users,
       (select rtrim(concat(case when u.id is not null then w.name || ',' end,
                            string_agg(w2.name, ',') || ',',
                            case when p.everyone_can_read then c.everyone_role || ',' end
                            ), ',')
        from {DB_SCHEMA}.rights r inner join
             {DB_SCHEMA}.users u2 on r.id_user = u2.id inner join
             {DB_SCHEMA}.workspaces w2 on w2.id = u2.id_workspace
        where r.id_publication = p.id
          and r.type = 'write') can_write_users
from const c inner join
     {DB_SCHEMA}.workspaces w on (   w.name = c.workspace_name
                                  or c.workspace_name is null) inner join
     {DB_SCHEMA}.publications p on p.id_workspace = w.id
                           and (   p.type = c.pub_type
                                or c.pub_type is null) left join
     {DB_SCHEMA}.users u on u.id_workspace = w.id
;"""
    values = util.run_query(sql, (workspace_name,
                                  pub_type,
                                  ROLE_EVERYONE,
                                  ))
    infos = {(workspace_name,
              type,
              publication_name,): {'id': id_publication,
                                   'name': publication_name,
                                   'title': title,
                                   'uuid': uuid,
                                   'type': type,
                                   }
             for id_publication, workspace_name, type, publication_name, title, uuid, can_read_users, can_write_users
             in values}
    return infos


def insert_publication(workspace_name, info):
    id_workspace = workspaces.ensure_workspace(workspace_name)

    insert_publications_sql = f'''insert into {DB_SCHEMA}.publications as p
        (id_workspace, name, title, type, uuid, everyone_can_read, everyone_can_write) values
        (%s, %s, %s, %s, %s, %s, %s)
returning id
;'''

    data = (id_workspace,
            info.get("name"),
            info.get("title"),
            info.get("publ_type_name"),
            info.get("uuid"),
            True,
            True,
            )
    pub_id = util.run_query(insert_publications_sql, data)[0][0]

    return pub_id


def update_publication(workspace_name, info):
    id_workspace = workspaces.get_workspace_infos(workspace_name)[workspace_name]["id"]
    update_publications_sql = f'''update {DB_SCHEMA}.publications set
        title = coalesce(%s, title),
        everyone_can_read = coalesce(%s, everyone_can_read),
        everyone_can_write = coalesce(%s, everyone_can_write)
    where id_workspace = %s
      and name = %s
      and type = %s
    returning id
    ;'''

    data = (info.get("title"),
            True,
            True,
            id_workspace,
            info.get("name"),
            info.get("publ_type_name"),
            )
    pub_id = util.run_query(update_publications_sql, data)[0][0]
    return pub_id


def delete_publication(workspace_name, type, name):
    workspace_info = workspaces.get_workspace_infos(workspace_name).get(workspace_name)
    if workspace_info:
        id_workspace = workspace_info["id"]
        sql = f"""delete from {DB_SCHEMA}.publications p where p.id_workspace = %s and p.name = %s and p.type = %s;"""
        util.run_statement(sql, (id_workspace,
                                 name,
                                 type,))
    else:
        logger.warning(f'Deleting publication for NON existing workspace. workspace_name={workspace_name}, pub_name={name}, type={type}')
