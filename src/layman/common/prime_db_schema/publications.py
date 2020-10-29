import logging

from . import util, workspaces, users
from layman import settings, LaymanError

logger = logging.getLogger(__name__)

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
ROLE_EVERYONE = settings.RIGHTS_EVERYONE_ROLE


def get_publication_infos(workspace_name=None, pub_type=None):
    sql = f"""with const as (select %s workspace_name, %s pub_type, %s everyone_role)
select w.name as workspace_name,
       p.type,
       p.name,
       p.title,
       p.uuid::text,
       (select rtrim(concat(case when u.id is not null then w.name || ', ' end,
                            string_agg(w2.name, ', ') || ', ',
                            case when p.everyone_can_read then c.everyone_role || ', ' end
                            ), ', ')
        from {DB_SCHEMA}.rights r inner join
             {DB_SCHEMA}.users u2 on r.id_user = u2.id inner join
             {DB_SCHEMA}.workspaces w2 on w2.id = u2.id_workspace
        where r.id_publication = p.id
          and r.type = 'read') can_read_users,
       (select rtrim(concat(case when u.id is not null then w.name || ', ' end,
                            string_agg(w2.name, ', ') || ', ',
                            case when p.everyone_can_read then c.everyone_role || ', ' end
                            ), ', ')
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
    infos = {layername: {'name': layername,
                         'title': title,
                         'uuid': uuid,
                         'type': type,
                         'access_rights': {'read': can_read_users,
                                           'write': can_write_users}
                         }
             for workspace_name, type, layername, title, uuid, can_read_users, can_write_users
             in values}
    return infos


def only_valid_names(users_list):
    usernames_for_chesk = users_list.copy()
    usernames_for_chesk.discard(ROLE_EVERYONE)
    for username in usernames_for_chesk:
        info = users.get_user_infos(username)
        if not info:
            raise LaymanError(43, {f'Not valid username. Username={username}'})


def at_least_one_can_write(can_write):
    if not can_write:
        raise LaymanError(43, {f'At least one user have to have write rights.'})


def who_can_write_can_read(can_read, can_write):
    if ROLE_EVERYONE not in can_read and can_write.difference(can_read):
        raise LaymanError(43, {f'All users who have write rights have to have also read rights. Who is missing={can_write.difference(can_read)}'})


def i_can_still_write(actor_name, can_write):
    if ROLE_EVERYONE not in can_write and actor_name not in can_write:
        raise LaymanError(43, {f'After the operation, the actor has to have write right.'})


def check_rights_axioms(can_read, can_write, actor_name):
    only_valid_names(can_read)
    only_valid_names(can_write)
    at_least_one_can_write(can_write)
    who_can_write_can_read(can_read, can_write)
    i_can_still_write(actor_name, can_write)


def check_publication_info(workspace_name, info):
    try:
        check_rights_axioms(info['access_rights']['read'],
                            info['access_rights']['write'],
                            info.get("actor_name"),
                            )
    except LaymanError as exc_info:
        raise LaymanError(43, {'workspace_name': workspace_name,
                               'publication_name': info.get("name"),
                               'access_rights': {
                                   'read': info['access_rights']['read'],
                                   'write': info['access_rights']['write'], },
                               'message': exc_info.data,
                               })


def insert_publication(workspace_name, info):
    id_workspace = workspaces.ensure_workspace(workspace_name)
    check_publication_info(workspace_name, info)

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
    pub_id = util.run_query(insert_publications_sql, data)

    # TODO insert rights into rights table
    return pub_id


def update_publication(workspace_name, info):
    id_workspace = workspaces.get_workspace_infos(workspace_name)[workspace_name]["id"]
    # check_publication_info(workspace_name, info)

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
            ROLE_EVERYONE in (info.get("can_read") or set()),
            ROLE_EVERYONE in (info.get("can_write") or set()),
            id_workspace,
            info.get("name"),
            info.get("publ_type_name"),
            )
    pub_id = util.run_query(update_publications_sql, data)
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
        logger.warning(f'Deleting publication for NON existing workspace. workspace_name={username}, pub_name={name}, type={type}')
