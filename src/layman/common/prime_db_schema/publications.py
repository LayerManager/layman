import logging
import psycopg2.extras

from layman import settings, LaymanError
from layman.common import get_publications_consts as consts
from . import util, workspaces, users, rights

logger = logging.getLogger(__name__)

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
ROLE_EVERYONE = settings.RIGHTS_EVERYONE_ROLE
psycopg2.extras.register_uuid()


def get_publication_infos(workspace_name=None, pub_type=None, style_type=None,
                          reader=None, writer=None,
                          full_text_filter=None,
                          bbox_filter=None,
                          order_by_list=None,
                          ordering_full_text=None,
                          ordering_bbox=None,
                          ):
    order_by_list = order_by_list or []

    where_params_def = [
        (workspace_name, 'w.name = %s', (workspace_name,)),
        (pub_type, 'p.type = %s', (pub_type,)),
        (style_type, 'p.style_type::text = %s', (style_type,)),
        (reader == settings.ANONYM_USER, 'p.everyone_can_read = TRUE', tuple()),
        (reader and reader != settings.ANONYM_USER, f"""(p.everyone_can_read = TRUE
                        or (u.id is not null and w.name = %s)
                        or EXISTS(select 1
                                  from {DB_SCHEMA}.rights r inner join
                                       {DB_SCHEMA}.users u2 on r.id_user = u2.id inner join
                                       {DB_SCHEMA}.workspaces w2 on w2.id = u2.id_workspace
                                  where r.id_publication = p.id
                                    and r.type = 'read'
                                    and w2.name = %s))""", (reader, reader,)),
        (writer == settings.ANONYM_USER, 'p.everyone_can_write = TRUE', tuple()),
        (writer and writer != settings.ANONYM_USER, f"""(p.everyone_can_write = TRUE
                        or (u.id is not null and w.name = %s)
                        or EXISTS(select 1
                                  from {DB_SCHEMA}.rights r inner join
                                       {DB_SCHEMA}.users u2 on r.id_user = u2.id inner join
                                       {DB_SCHEMA}.workspaces w2 on w2.id = u2.id_workspace
                                  where r.id_publication = p.id
                                    and r.type = 'write'
                                    and w2.name = %s))""", (writer, writer,)),
        (full_text_filter, '_prime_schema.my_unaccent(p.title) @@ to_tsquery(unaccent(%s))', (full_text_filter,)),
        (bbox_filter, 'p.bbox && ST_MakeBox2D(ST_MakePoint(%s, %s), ST_MakePoint(%s, %s))', bbox_filter),
    ]

    order_by_definition = {
        consts.ORDER_BY_FULL_TEXT: ('ts_rank_cd(_prime_schema.my_unaccent(p.title), to_tsquery(unaccent(%s))) DESC',
                                    (ordering_full_text,)),
        consts.ORDER_BY_TITLE: ('unaccent(p.title) ASC', tuple()),
        consts.ORDER_BY_LAST_CHANGE: ('updated_at DESC', tuple()),
        consts.ORDER_BY_BBOX: ("""
            -- A∩B / (A + B)
            CASE
                -- if there is any intersection
                WHEN p.bbox && ST_MakeBox2D(ST_MakePoint(%s, %s),
                                            ST_MakePoint(%s, %s))
                    THEN
                        -- in cases, when area of intersection is 0, we want it rank higher than no intersection
                        GREATEST(st_area(st_intersection(p.bbox, ST_MakeBox2D(ST_MakePoint(%s, %s),
                                                                              ST_MakePoint(%s, %s)))),
                                 1)
                        -- we have to solve division by 0
                        / (GREATEST(st_area(p.bbox), 1) +
                           GREATEST(st_area(ST_MakeBox2D(ST_MakePoint(%s, %s),
                                                         ST_MakePoint(%s, %s))),
                                    1)
                           )
                -- if there is no intersection, result is 0 in all cases
                ELSE
                    0
            END DESC
            """, ordering_bbox + ordering_bbox + ordering_bbox if ordering_bbox else tuple()),
    }

    assert all(ordering_item in order_by_definition.keys() for ordering_item in order_by_list)

    #########################################################
    # SELECT clause
    select_clause = f"""
select p.id as id_publication,
       w.name as workspace_name,
       p.type,
       p.name,
       p.title,
       p.uuid::text,
       p.style_type,
       p.updated_at,
       ST_XMIN(p.bbox) as xmin,
       ST_YMIN(p.bbox) as ymin,
       ST_XMAX(p.bbox) as xmax,
       ST_YMAX(p.bbox) as ymax,
       (select rtrim(concat(case when u.id is not null then w.name || ',' end,
                            string_agg(w2.name, ',') || ',',
                            case when p.everyone_can_read then %s || ',' end
                            ), ',')
        from {DB_SCHEMA}.rights r inner join
             {DB_SCHEMA}.users u2 on r.id_user = u2.id inner join
             {DB_SCHEMA}.workspaces w2 on w2.id = u2.id_workspace
        where r.id_publication = p.id
          and r.type = 'read') can_read_users,
       (select rtrim(concat(case when u.id is not null then w.name || ',' end,
                            string_agg(w2.name, ',') || ',',
                            case when p.everyone_can_write then %s || ',' end
                            ), ',')
        from {DB_SCHEMA}.rights r inner join
             {DB_SCHEMA}.users u2 on r.id_user = u2.id inner join
             {DB_SCHEMA}.workspaces w2 on w2.id = u2.id_workspace
        where r.id_publication = p.id
          and r.type = 'write') can_write_users
from {DB_SCHEMA}.workspaces w inner join
     {DB_SCHEMA}.publications p on p.id_workspace = w.id left join
     {DB_SCHEMA}.users u on u.id_workspace = w.id
"""
    select_params = (ROLE_EVERYONE, ROLE_EVERYONE, )

    #########################################################
    # WHERE clause
    where_params = tuple()
    where_parts = list()
    for (value, where_part, params, ) in where_params_def:
        if value:
            where_parts.append(where_part)
            where_params = where_params + params
    where_clause = ''
    if where_parts:
        where_clause = 'WHERE ' + '\n  AND '.join(where_parts) + '\n'

    #########################################################
    # ORDER BY clause
    order_by_params = tuple()
    order_by_parts = list()
    for order_by_part in order_by_list:
        order_by_parts.append(order_by_definition[order_by_part][0])
        order_by_params = order_by_params + order_by_definition[order_by_part][1]

    order_by_parts.append('w.name ASC')
    order_by_parts.append('p.name ASC')
    order_by_clause = 'ORDER BY ' + ', '.join(order_by_parts)

    #########################################################
    # Put it together
    sql_params = select_params + where_params + order_by_params
    select = select_clause + where_clause + order_by_clause
    values = util.run_query(select, sql_params)

    # print(f'get_publication_infos:\n\n order_by_clause={order_by_clause},\n where_clause={where_clause},\n sql_params={sql_params},'
    #       f'\n order_by_list={order_by_list},\n full_text_ordering={full_text_ordering}')

    infos = {(workspace_name,
              type,
              publication_name,): {'id': id_publication,
                                   'name': publication_name,
                                   'title': title,
                                   'uuid': uuid,
                                   'type': type,
                                   'style_type': style_type,
                                   'updated_at': updated_at,
                                   'bounding_box': [xmin, ymin, xmax, ymax],
                                   'access_rights': {'read': can_read_users.split(','),
                                                     'write': can_write_users.split(',')}
                                   }
             for id_publication, workspace_name, type, publication_name, title, uuid, style_type, updated_at, xmin, ymin, xmax, ymax,
             can_read_users, can_write_users
             in values}
    return infos


def only_valid_names(users_list):
    usernames_for_chesk = set(users_list)
    usernames_for_chesk.discard(ROLE_EVERYONE)
    for username in usernames_for_chesk:
        info = users.get_user_infos(username)
        if not info:
            raise LaymanError(43, f'Not existing user. Username={username}')


def at_least_one_can_write(can_write):
    if not can_write:
        raise LaymanError(43, f'At least one user have to have write rights.')


def who_can_write_can_read(can_read, can_write):
    if ROLE_EVERYONE not in can_read and set(can_write).difference(can_read):
        raise LaymanError(43, f'All users who have write rights have to have also read rights. Who is missing={set(can_write).difference(can_read)}')


def i_can_still_write(actor_name, can_write):
    if ROLE_EVERYONE not in can_write and actor_name not in can_write:
        raise LaymanError(43, f'After the operation, the actor has to have write right.')


def owner_can_still_write(owner,
                          can_write,
                          ):
    if owner and ROLE_EVERYONE not in can_write and owner not in can_write:
        raise LaymanError(43, f'Owner of the personal workspace have to keep write right.')


def check_rights_axioms(can_read,
                        can_write,
                        actor_name,
                        owner,
                        can_read_old=None,
                        can_write_old=None):
    if can_read:
        only_valid_names(can_read)
    if can_write:
        only_valid_names(can_write)
        owner_can_still_write(owner, can_write)
        at_least_one_can_write(can_write)
        i_can_still_write(actor_name, can_write)
    if can_read or can_write:
        can_read_check = can_read or can_read_old
        can_write_check = can_write or can_write_old
        who_can_write_can_read(can_read_check, can_write_check)


def check_publication_info(workspace_name, info):
    owner_info = users.get_user_infos(workspace_name).get(workspace_name)
    info["owner"] = owner_info and owner_info["username"]
    try:
        check_rights_axioms(info['access_rights'].get('read'),
                            info['access_rights'].get('write'),
                            info["actor_name"],
                            info["owner"],
                            info['access_rights'].get('read_old'),
                            info['access_rights'].get('write_old'),
                            )
    except LaymanError as exc_info:
        raise LaymanError(43, {'workspace_name': workspace_name,
                               'publication_name': info.get("name"),
                               'access_rights': {
                                   'read': info['access_rights'].get('read'),
                                   'write': info['access_rights'].get('write'), },
                               'actor_name': info.get("actor_name"),
                               'owner': info["owner"],
                               'message': exc_info.data,
                               }) from exc_info


def clear_roles(users_list, workspace_name):
    result_set = set(users_list)
    result_set.discard(ROLE_EVERYONE)
    user_info = users.get_user_infos(workspace_name)
    if user_info:
        result_set.discard(workspace_name)
    return result_set


def insert_publication(workspace_name, info):
    id_workspace = workspaces.ensure_workspace(workspace_name)
    check_publication_info(workspace_name, info)

    insert_publications_sql = f'''insert into {DB_SCHEMA}.publications as p
        (id_workspace, name, title, type, uuid, style_type, everyone_can_read, everyone_can_write, updated_at) values
        (%s, %s, %s, %s, %s, %s, %s, %s,  current_timestamp)
returning id
;'''

    data = (id_workspace,
            info.get("name"),
            info.get("title"),
            info.get("publ_type_name"),
            info.get("uuid"),
            info.get('style_type'),
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

    access_rights_changes = dict()
    for right_type in right_type_list:
        access_rights_changes[right_type] = {
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
            access_rights_changes[right_type]['username_list_old'] = info_old["access_rights"][right_type]
            info["access_rights"][right_type + "_old"] = access_rights_changes[right_type]['username_list_old']
        check_publication_info(workspace_name, info)

        for right_type in right_type_list:
            if info['access_rights'].get(right_type):
                usernames_list = info["access_rights"].get(right_type)
                access_rights_changes[right_type]['EVERYONE'] = ROLE_EVERYONE in usernames_list
                usernames_list_clear = clear_roles(usernames_list, workspace_name)
                usernames_old_list_clear = clear_roles(access_rights_changes[right_type]['username_list_old'], workspace_name)
                access_rights_changes[right_type]['add'] = usernames_list_clear.difference(usernames_old_list_clear)
                access_rights_changes[right_type]['remove'] = usernames_old_list_clear.difference(usernames_list_clear)

    update_publications_sql = f'''update {DB_SCHEMA}.publications set
    title = coalesce(%s, title),
    style_type = coalesce(%s, style_type),
    everyone_can_read = coalesce(%s, everyone_can_read),
    everyone_can_write = coalesce(%s, everyone_can_write),
    updated_at =  current_timestamp
where id_workspace = %s
  and name = %s
  and type = %s
returning id
;'''

    data = (info.get("title"),
            info.get('style_type'),
            access_rights_changes['read']['EVERYONE'],
            access_rights_changes['write']['EVERYONE'],
            id_workspace,
            info.get("name"),
            info.get("publ_type_name"),
            )
    pub_id = util.run_query(update_publications_sql, data)[0][0]

    for right_type in right_type_list:
        rights.insert_rights(pub_id, access_rights_changes[right_type]['add'], right_type)
        rights.remove_rights(pub_id, access_rights_changes[right_type]['remove'], right_type)

    return pub_id


def delete_publication(workspace_name, type, name):
    workspace_info = workspaces.get_workspace_infos(workspace_name).get(workspace_name)
    if workspace_info:
        id_publication = get_publication_infos(workspace_name, type).get((workspace_name, type, name), dict()).get("id")
        if id_publication:
            rights.delete_rights_for_publication(id_publication)
            id_workspace = workspace_info["id"]
            sql = f"""delete from {DB_SCHEMA}.publications p where p.id_workspace = %s and p.name = %s and p.type = %s;"""
            util.run_statement(sql, (id_workspace,
                                     name,
                                     type,))
        else:
            logger.warning(f'Deleting NON existing publication. workspace_name={workspace_name}, type={type}, pub_name={name}')
    else:
        logger.warning(f'Deleting publication for NON existing workspace. workspace_name={workspace_name}, type={type}, pub_name={name}')


def set_bbox(workspace, publication_type, publication, bbox):
    query = f'''update {DB_SCHEMA}.publications set
    bbox = ST_MakeBox2D(ST_Point(%s, %s), ST_Point(%s ,%s))
    where type = %s
      and name = %s
      and id_workspace = (select w.id from {DB_SCHEMA}.workspaces w where w.name = %s);'''
    params = bbox + (publication_type, publication, workspace,)
    util.run_statement(query, params)
