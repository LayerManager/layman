import logging
import psycopg2.extras

from . import util, workspaces, users, rights
from layman import settings, LaymanError

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
                                   'access_rights': {'read': [x for x in can_read_users.split(',')],
                                                     'write': [x for x in can_write_users.split(',')]}
                                   }
             for id_publication, workspace_name, type, publication_name, title, uuid, can_read_users, can_write_users
             in values}
    return infos


def clear_roles(users_list, workspace_name):
    result_set = set(users_list)
    result_set.discard(ROLE_EVERYONE)
    user_info = users.get_user_infos(workspace_name)
    if user_info:
        result_set.discard(workspace_name)
    return result_set


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
            ROLE_EVERYONE in info['access_rights']['read'],
            ROLE_EVERYONE in info['access_rights']['write'],
            )
    pub_id = util.run_query(insert_publications_sql, data)[0][0]

    read_users = clear_roles(info['access_rights']['read'], workspace_name)
    write_users = clear_roles(info['access_rights']['write'], workspace_name)
    rights.insert_rights(pub_id,
                         read_users,
                         'read')
    rights.insert_rights(pub_id,
                         write_users,
                         'write')
    return pub_id


def update_publication(workspace_name, info):
    id_workspace = workspaces.get_workspace_infos(workspace_name)[workspace_name]["id"]
    right_type_list = ['read', 'write']

    access_rights_det = dict()
    for right_type in right_type_list:
        access_rights_det[right_type] = {
            'EVERYONE': None,
            'add': set(),
            'remove': set(),
        }

    if info.get("access_rights") and (info["access_rights"].get("read") or info["access_rights"].get("write")):
        info_old = get_publication_infos(workspace_name,
                                         info["publ_type_name"])[(workspace_name,
                                                                  info["publ_type_name"],
                                                                  info["name"],)]
        for right_type in right_type_list:
            access_rights_det[right_type]['username_list_old'] = info_old["access_rights"][right_type]
            info["access_rights"][right_type + "_old"] = access_rights_det[right_type]['username_list_old']

        for right_type in right_type_list:
            if info['access_rights'].get(right_type):
                usernames_list = info["access_rights"].get(right_type)
                access_rights_det[right_type]['EVERYONE'] = ROLE_EVERYONE in usernames_list
                usernames_list_clear = clear_roles(usernames_list, workspace_name)
                usernames_old_list_clear = clear_roles(access_rights_det[right_type]['username_list_old'], workspace_name)
                access_rights_det[right_type]['add'] = usernames_list_clear.difference(usernames_old_list_clear)
                access_rights_det[right_type]['remove'] = usernames_old_list_clear.difference(usernames_list_clear)

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
            access_rights_det['read']['EVERYONE'],
            access_rights_det['write']['EVERYONE'],
            id_workspace,
            info.get("name"),
            info.get("publ_type_name"),
            )
    pub_id = util.run_query(update_publications_sql, data)[0][0]

    for right_type in right_type_list:
        rights.insert_rights(pub_id, access_rights_det[right_type]['add'], right_type)
        rights.remove_rights(pub_id, access_rights_det[right_type]['remove'], right_type)

    return pub_id


def delete_publication(workspace_name, type, name):
    workspace_info = workspaces.get_workspace_infos(workspace_name).get(workspace_name)
    if workspace_info:
        id_publication = get_publication_infos(workspace_name, type)[(workspace_name, type, name)]["id"]
        rights.delete_rights_for_publication(id_publication)
        id_workspace = workspace_info["id"]
        sql = f"""delete from {DB_SCHEMA}.publications p where p.id_workspace = %s and p.name = %s and p.type = %s;"""
        util.run_statement(sql, (id_workspace,
                                 name,
                                 type,))
    else:
        logger.warning(f'Deleting publication for NON existing workspace. workspace_name={workspace_name}, pub_name={name}, type={type}')
