from dataclasses import dataclass
import logging
import psycopg2.extras

import crs as crs_def
from db import util as db_util, TableUri
from layman import settings, LaymanError
from layman.authn import is_user_with_name
from layman.common import get_publications_consts as consts, bbox as bbox_util
from . import workspaces, users, rights

logger = logging.getLogger(__name__)

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA
ROLE_EVERYONE = settings.RIGHTS_EVERYONE_ROLE
DEFAULT_BBOX_CRS = 'EPSG:3857'
psycopg2.extras.register_uuid()


@dataclass
class CalculatedColumnType:
    alias: str
    definition: str
    params: tuple = tuple()


def get_publication_infos(workspace_name=None, pub_type=None, style_type=None,
                          reader=None, writer=None,
                          ):
    return get_publication_infos_with_metainfo(workspace_name, pub_type, style_type,
                                               reader, writer,)['items']


def get_publication_infos_with_metainfo(workspace_name=None, pub_type=None, style_type=None,
                                        reader=None, writer=None,
                                        limit=None, offset=None,
                                        full_text_filter=None,
                                        bbox_filter=None,
                                        bbox_filter_crs=None,
                                        order_by_list=None,
                                        ordering_full_text=None,
                                        ordering_bbox=None,
                                        ordering_bbox_crs=None,
                                        ):
    order_by_list = order_by_list or []

    full_text_tsquery = db_util.to_tsquery_string(full_text_filter) if full_text_filter else None
    full_text_like = '%' + full_text_filter + '%' if full_text_filter else None
    ordering_full_text_tsquery = db_util.to_tsquery_string(ordering_full_text) if ordering_full_text else None

    ordering_bbox_srid = db_util.get_internal_srid(ordering_bbox_crs)
    filtering_bbox_srid = db_util.get_internal_srid(bbox_filter_crs)

    bbox_filter_where_part = secure_bbox_transform(bbox_filter_crs)
    bbox_filter_where_part += ' && ST_MakeBox2D(ST_MakePoint(%s, %s), ST_MakePoint(%s, %s))'

    where_params_def = [
        (workspace_name, 'w.name = %s', (workspace_name,)),
        (pub_type, 'p.type = %s', (pub_type,)),
        (style_type, 'p.style_type::text = %s', (style_type,)),
        (reader and not is_user_with_name(reader), 'p.everyone_can_read = TRUE', tuple()),
        (is_user_with_name(reader), f"""(p.everyone_can_read = TRUE
                        or (u.id is not null and w.name = %s)
                        or EXISTS(select 1
                                  from {DB_SCHEMA}.rights r inner join
                                       {DB_SCHEMA}.users u2 on r.id_user = u2.id inner join
                                       {DB_SCHEMA}.workspaces w2 on w2.id = u2.id_workspace
                                  where r.id_publication = p.id
                                    and r.type = 'read'
                                    and w2.name = %s))""", (reader, reader,)),
        (writer and not is_user_with_name(writer), 'p.everyone_can_write = TRUE', tuple()),
        (is_user_with_name(writer), f"""(p.everyone_can_write = TRUE
                        or (u.id is not null and w.name = %s)
                        or EXISTS(select 1
                                  from {DB_SCHEMA}.rights r inner join
                                       {DB_SCHEMA}.users u2 on r.id_user = u2.id inner join
                                       {DB_SCHEMA}.workspaces w2 on w2.id = u2.id_workspace
                                  where r.id_publication = p.id
                                    and r.type = 'write'
                                    and w2.name = %s))""", (writer, writer,)),
        (full_text_filter, '(_prime_schema.my_unaccent(p.title) @@ to_tsquery(unaccent(%s))'
                           'or lower(unaccent(p.title)) like lower(unaccent(%s)))', (full_text_tsquery, full_text_like,)),
        (bbox_filter, bbox_filter_where_part, (filtering_bbox_srid, ) + bbox_filter if bbox_filter else None, ),
    ]

    order_by_definition = {
        consts.ORDER_BY_FULL_TEXT: ('ts_rank_cd(_prime_schema.my_unaccent(p.title), to_tsquery(unaccent(%s))) DESC',
                                    (ordering_full_text_tsquery,)),
        consts.ORDER_BY_TITLE: ("regexp_replace(lower(unaccent(p.title)), '[^a-zA-Z0-9 ]', '', 'g') ASC", tuple()),
        consts.ORDER_BY_LAST_CHANGE: ('updated_at DESC', tuple()),
        consts.ORDER_BY_BBOX: ("""
            -- A∩B / (A + B)
            CASE
                -- if there is any intersection
                WHEN p.bbox_for_ordering && consts.ordering_bbox
                    THEN
                        -- in cases, when area of intersection is 0, we want it rank higher than no intersection
                        GREATEST(st_area(st_intersection(p.bbox_for_ordering, consts.ordering_bbox)),
                                 0.00001)
                        -- we have to solve division by 0
                        / (GREATEST(st_area(p.bbox_for_ordering), 0.00001) +
                           GREATEST(st_area(consts.ordering_bbox), 0.00001)
                           )
                -- if there is no intersection, result is 0 in all cases
                ELSE
                    0
            END DESC
            """, tuple()),
    }

    assert all(ordering_item in order_by_definition for ordering_item in order_by_list)

    calculated_columns = []
    ordering_bbox_clause = ''
    with_consts_params = tuple()
    if ordering_bbox_crs:
        bbox_for_ordering_def = secure_bbox_transform(ordering_bbox_crs)
        ordering_bbox_clause = f"""ST_SetSRID(ST_MakeBox2D(ST_MakePoint(%s, %s),ST_MakePoint(%s, %s)), %s) ordering_bbox"""
        calculated_columns.append(CalculatedColumnType(alias="bbox_for_ordering",
                                                       definition=bbox_for_ordering_def,
                                                       params=(ordering_bbox_srid, )))
        with_consts_params = ordering_bbox + (ordering_bbox_srid, )

    calculated_columns_str = ', '.join([f"{calculated_column.definition} as {calculated_column.alias}" for calculated_column in calculated_columns])
    calculated_columns_str = f", {calculated_columns_str}" if calculated_columns_str else ""

    #########################################################
    # SELECT clause
    select_clause = f"""
with publs as (
select * {calculated_columns_str} from {DB_SCHEMA}.publications p
),
consts as (
    select {ordering_bbox_clause}
)
select p.id as id_publication,
       w.name as workspace_name,
       p.type,
       p.name,
       p.title,
       p.uuid::text,
       p.geodata_type,
       p.style_type,
       p.image_mosaic,
       p.updated_at,
       ST_XMIN(p.bbox) as xmin,
       ST_YMIN(p.bbox) as ymin,
       ST_XMAX(p.bbox) as xmax,
       ST_YMAX(p.bbox) as ymax,
       p.srid as srid,
       PGP_SYM_DECRYPT(p.external_table_uri, p.uuid::text)::json external_table_uri,
       (select rtrim(concat(case when u.id is not null then w.name || ',' end,
                            string_agg(COALESCE(w2.name, r.role_name), ',' ORDER BY COALESCE(w2.name, r.role_name)) || ',',
                            case when p.everyone_can_read then %s || ',' end
                            ), ',')
        from {DB_SCHEMA}.rights r left join
             {DB_SCHEMA}.users u2 on r.id_user = u2.id left join
             {DB_SCHEMA}.workspaces w2 on w2.id = u2.id_workspace
        where r.id_publication = p.id
          and r.type = 'read') read_users_roles,
       (select rtrim(concat(case when u.id is not null then w.name || ',' end,
                            string_agg(COALESCE(w2.name, r.role_name), ',' ORDER BY COALESCE(w2.name, r.role_name)) || ',',
                            case when p.everyone_can_write then %s || ',' end
                            ), ',')
        from {DB_SCHEMA}.rights r left join
             {DB_SCHEMA}.users u2 on r.id_user = u2.id left join
             {DB_SCHEMA}.workspaces w2 on w2.id = u2.id_workspace
        where r.id_publication = p.id
          and r.type = 'write') write_users_roles,
       (select json_agg(json_build_object(
                   'name', ml.layer_name,
                   'workspace', ml.layer_workspace,
                   'index', ml.layer_index,
                   'uuid', lr.uuid
                   ) order by ml.layer_index, ml.layer_workspace, ml.layer_name)
        from {DB_SCHEMA}.map_layer ml left join
             {DB_SCHEMA}.workspaces lr_ws on ml.layer_workspace = lr_ws.name left join
             {DB_SCHEMA}.publications lr on ml.layer_name = lr.name
                                        and lr_ws.id = lr.id_workspace
        where ml.id_map = p.id) map_layers,
       (select json_agg(json_build_object(
           'name', map_name,
           'workspace', map_ws_name
           ) order by map_ws_name, map_name)
        from (
                 select distinct map.name    map_name,
                                 map_ws.name map_ws_name
                 from {DB_SCHEMA}.map_layer ml left join
                     {DB_SCHEMA}.publications map on ml.id_map = map.id inner join
                     {DB_SCHEMA}.workspaces map_ws on map.id_workspace = map_ws.id
                 where ml.layer_workspace = w.name
                   and ml.layer_name = p.name
                 order by map_ws_name, map_name
             ) tmp_layer_maps
           ) layer_maps,
       p.wfs_wms_status,
       count(*) OVER() AS full_count
from {DB_SCHEMA}.workspaces w inner join
     publs p on p.id_workspace = w.id left join
     {DB_SCHEMA}.users u on u.id_workspace = w.id,
     consts
"""
    select_params = (ROLE_EVERYONE, ROLE_EVERYONE, )

    #########################################################
    # WHERE clause
    where_params = tuple()
    where_parts = []
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
    order_by_parts = []
    for order_by_part in order_by_list:
        order_by_parts.append(order_by_definition[order_by_part][0])
        order_by_params = order_by_params + order_by_definition[order_by_part][1]

    order_by_parts.append('w.name ASC')
    order_by_parts.append('p.name ASC')
    order_by_parts.append('p.type ASC')
    order_by_clause = 'ORDER BY ' + ', '.join(order_by_parts)

    #########################################################
    # Pagination clause
    pagination_params = tuple()
    pagination_clause = ''

    if limit is not None:
        assert limit >= 0
        assert isinstance(limit, int)
        pagination_clause = pagination_clause + f' LIMIT {limit} '
    if offset is not None:
        assert offset >= 0
        assert isinstance(offset, int)
        pagination_clause = pagination_clause + f' OFFSET {offset} '

    #########################################################
    # Put it together
    with_publications_params = tuple(param for column in calculated_columns for param in column.params)
    sql_params = with_publications_params + with_consts_params + select_params + where_params + order_by_params + pagination_params
    select = select_clause + where_clause + order_by_clause + pagination_clause
    values = db_util.run_query(select, sql_params)

    # print(f'get_publication_infos:\n\nselect={select}\n\nsql_params={sql_params}\n\n&&&&&&&&&&&&&&&&&')

    infos = {(workspace_name,
              publication_type,
              publication_name,): {'id': id_publication,
                                   'name': publication_name,
                                   'title': title,
                                   'uuid': uuid,
                                   'type': publication_type,
                                   'geodata_type': geodata_type,
                                   '_style_type': style_type,
                                   'image_mosaic': image_mosaic,
                                   'updated_at': updated_at,
                                   '_table_uri': TableUri(
                                       db_uri_str=external_table_uri['db_uri_str'],
                                       schema=external_table_uri['schema'],
                                       table=external_table_uri['table'],
                                       geo_column=external_table_uri['geo_column'],
                                       primary_key_column=external_table_uri['primary_key_column'],
                                   ) if external_table_uri else None,
                                   'original_data_source': settings.EnumOriginalDataSource.TABLE.value if external_table_uri else settings.EnumOriginalDataSource.FILE.value,
                                   'native_bounding_box': [xmin, ymin, xmax, ymax],
                                   'native_crs': db_util.get_crs_from_srid(srid, use_internal_srid=True) if srid else None,
                                   'access_rights': {'read': read_users_roles.split(','),
                                                     'write': write_users_roles.split(',')},
                                   '_map_layers': map_layers or [],
                                   '_layer_maps': layer_maps or [],
                                   '_wfs_wms_status': settings.EnumWfsWmsStatus(wfs_wms_status) if wfs_wms_status else None,
                                   }
             for id_publication, workspace_name, publication_type, publication_name, title, uuid, geodata_type, style_type, image_mosaic, updated_at, xmin, ymin, xmax, ymax,
             srid, external_table_uri, read_users_roles, write_users_roles, map_layers, layer_maps, wfs_wms_status, _
             in values}

    infos = {key: {**value,
                   'bounding_box': list(bbox_util.transform(value['native_bounding_box'],
                                                            value['native_crs'],
                                                            DEFAULT_BBOX_CRS))
                   if value['native_bounding_box'][0]
                   and value['native_crs']
                   and DEFAULT_BBOX_CRS != value['native_crs']
                   else value['native_bounding_box'],
                   }
             for key, value in infos.items()}

    if values:
        total_count = values[0][-1]
    else:
        count_clause = f"""
        select count(*) AS full_count
        from {DB_SCHEMA}.workspaces w inner join
             {DB_SCHEMA}.publications p on p.id_workspace = w.id left join
             {DB_SCHEMA}.users u on u.id_workspace = w.id
        """
        sql_params = where_params
        select = count_clause + where_clause
        count = db_util.run_query(select, sql_params)
        total_count = count[0][-1]

    if infos:
        start = offset + 1 if offset else 1
        content_range = (start, start + len(infos) - 1)
    else:
        content_range = (0, 0)

    result = {'items': infos,
              'total_count': total_count,
              'content_range': content_range,
              }
    return result


def secure_bbox_transform(bbox_crs):
    if bbox_crs and bbox_crs in crs_def.CRSDefinitions and crs_def.CRSDefinitions[bbox_crs].world_bounds:
        bbox_sql = f"""ST_TRANSFORM(ST_SetSRID(case """
        for world_bound_crs, world_bound_bbox in crs_def.CRSDefinitions[bbox_crs].world_bounds.items():
            world_bound_srid = db_util.get_internal_srid(world_bound_crs)
            bbox_sql += f'''
                              when p.srid = {world_bound_srid} then ST_MakeBox2D(
                        ST_MakePoint(least(greatest(ST_XMIN(p.bbox), {world_bound_bbox[0]}), {world_bound_bbox[2]}),
                                            least(greatest(ST_YMIN(p.bbox), {world_bound_bbox[1]}), {world_bound_bbox[3]})
                            ),
                        ST_MakePoint(greatest(least(ST_XMAX(p.bbox), {world_bound_bbox[2]}), {world_bound_bbox[0]}),
                                            greatest(least(ST_YMAX(p.bbox), {world_bound_bbox[3]}), {world_bound_bbox[1]})
                            ))
                '''
        bbox_sql += f'else p.bbox end, p.srid), %s)'
    else:
        bbox_sql = 'ST_TRANSFORM(ST_SetSRID(p.bbox, p.srid), %s)'
    return bbox_sql


def only_valid_user_names(users_list):
    usernames_for_check = set(users_list)
    for username in usernames_for_check:
        info = users.get_user_infos(username)
        if not info:
            raise LaymanError(43, f'Not existing user. Username={username}')


# pylint: disable=unused-argument
def only_valid_role_names(roles_list):
    pass


def at_least_one_can_write(user_names, role_names):
    if not user_names and ROLE_EVERYONE not in role_names:
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


def split_user_and_role_names(user_and_role_names):
    user_names = [name for name in user_and_role_names if any(letter.islower() for letter in name)]
    role_names = [name for name in user_and_role_names if name not in user_names]
    return user_names, role_names


def check_rights_axioms(can_read,
                        can_write,
                        actor_name,
                        owner,
                        can_read_old=None,
                        can_write_old=None):
    if can_read:
        read_users, read_roles = split_user_and_role_names(can_read)
        only_valid_user_names(read_users)
        only_valid_role_names(read_roles)
    if can_write:
        write_users, write_roles = split_user_and_role_names(can_write)
        only_valid_user_names(write_users)
        only_valid_role_names(write_roles)
        owner_can_still_write(owner, can_write)
        at_least_one_can_write(write_users, write_roles)
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


def get_user_and_role_names_for_db(users_and_roles_list, workspace_name):
    user_names, role_names = split_user_and_role_names(users_and_roles_list)

    users_set = set(user_names)
    user_info = users.get_user_infos(workspace_name)
    if user_info:
        users_set.discard(workspace_name)

    roles_set = set(role_names)
    roles_set.discard(ROLE_EVERYONE)

    return users_set, roles_set


def insert_publication(workspace_name, info):
    id_workspace = workspaces.ensure_workspace(workspace_name)
    check_publication_info(workspace_name, info)

    insert_publications_sql = f'''insert into {DB_SCHEMA}.publications as p
        (id_workspace, name, title, type, uuid, style_type, geodata_type, everyone_can_read, everyone_can_write, updated_at, image_mosaic, external_table_uri, wfs_wms_status) values
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, current_timestamp, %s, PGP_SYM_ENCRYPT(%s::text, %s::text), %s )
returning id
;'''

    external_table_uri = psycopg2.extras.Json({
        'db_uri_str': info["external_table_uri"].db_uri_str,
        'schema': info["external_table_uri"].schema,
        'table': info["external_table_uri"].table,
        'geo_column': info["external_table_uri"].geo_column,
        'primary_key_column': info["external_table_uri"].primary_key_column,
    }) if info.get("external_table_uri") else None

    data = (id_workspace,
            info.get("name"),
            info.get("title"),
            info.get("publ_type_name"),
            info.get("uuid"),
            info.get('style_type'),
            info.get('geodata_type'),
            ROLE_EVERYONE in info['access_rights']['read'],
            ROLE_EVERYONE in info['access_rights']['write'],
            info.get("image_mosaic"),
            external_table_uri,
            info.get("uuid"),
            info.get("wfs_wms_status")
            )
    pub_id = db_util.run_query(insert_publications_sql, data)[0][0]

    read_users, read_roles = get_user_and_role_names_for_db(info['access_rights']['read'], workspace_name)
    write_users, write_roles = get_user_and_role_names_for_db(info['access_rights']['write'], workspace_name)
    rights.insert_rights(pub_id,
                         read_users,
                         read_roles,
                         'read')
    rights.insert_rights(pub_id,
                         write_users,
                         write_roles,
                         'write')
    return pub_id


def update_publication(workspace_name, info):
    id_workspace = workspaces.get_workspace_infos(workspace_name)[workspace_name]["id"]
    right_type_list = ['read', 'write']

    access_rights_changes = {}
    for right_type in right_type_list:
        access_rights_changes[right_type] = {
            'EVERYONE': None,
            'add_users': set(),
            'add_roles': set(),
            'remove_users': set(),
            'remove_roles': set(),
        }

    external_table_uri = psycopg2.extras.Json({
        'db_uri_str': info["external_table_uri"].db_uri_str,
        'schema': info["external_table_uri"].schema,
        'table': info["external_table_uri"].table,
        'geo_column': info["external_table_uri"].geo_column,
        'primary_key_column': info["external_table_uri"].primary_key_column,
    }) if info.get("external_table_uri") else None

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
                usernames_list_clear, roles_list_clear = get_user_and_role_names_for_db(usernames_list, workspace_name)
                usernames_old_list_clear, roles_old_list_clear = get_user_and_role_names_for_db(access_rights_changes[right_type]['username_list_old'], workspace_name)
                access_rights_changes[right_type]['add_users'] = usernames_list_clear.difference(usernames_old_list_clear)
                access_rights_changes[right_type]['add_roles'] = roles_list_clear.difference(roles_old_list_clear)
                access_rights_changes[right_type]['remove_users'] = usernames_old_list_clear.difference(usernames_list_clear)
                access_rights_changes[right_type]['remove_roles'] = roles_old_list_clear.difference(roles_list_clear)

    update_publications_sql = f'''update {DB_SCHEMA}.publications set
    title = coalesce(%s, title),
    style_type = coalesce(%s, style_type),
    everyone_can_read = coalesce(%s, everyone_can_read),
    everyone_can_write = coalesce(%s, everyone_can_write),
    updated_at =  current_timestamp,
    image_mosaic = coalesce(%s, image_mosaic),
    external_table_uri = PGP_SYM_ENCRYPT(%s::text, uuid::text),
    geodata_type = coalesce(%s, geodata_type)
where id_workspace = %s
  and name = %s
  and type = %s
returning id
;'''

    data = (info.get("title"),
            info.get('style_type'),
            access_rights_changes['read']['EVERYONE'],
            access_rights_changes['write']['EVERYONE'],
            info.get("image_mosaic"),
            external_table_uri,
            info.get("geodata_type"),
            id_workspace,
            info.get("name"),
            info.get("publ_type_name"),
            )
    pub_id = db_util.run_query(update_publications_sql, data)[0][0]

    for right_type in right_type_list:
        rights.insert_rights(pub_id, access_rights_changes[right_type]['add_users'], access_rights_changes[right_type]['add_roles'], right_type)
        rights.remove_rights(pub_id, access_rights_changes[right_type]['remove_users'], access_rights_changes[right_type]['remove_roles'], right_type)

    return pub_id


def delete_publication(workspace_name, type, name):
    workspace_info = workspaces.get_workspace_infos(workspace_name).get(workspace_name)
    if workspace_info:
        id_publication = get_publication_infos(workspace_name, type).get((workspace_name, type, name), {}).get("id")
        if id_publication:
            rights.delete_rights_for_publication(id_publication)
            id_workspace = workspace_info["id"]
            sql = f"""delete from {DB_SCHEMA}.publications p where p.id_workspace = %s and p.name = %s and p.type = %s;"""
            db_util.run_statement(sql, (id_workspace,
                                        name,
                                        type,))
        else:
            logger.warning(f'Deleting NON existing publication. workspace_name={workspace_name}, type={type}, pub_name={name}')
    else:
        logger.warning(f'Deleting publication for NON existing workspace. workspace_name={workspace_name}, type={type}, pub_name={name}')


def set_bbox(workspace, publication_type, publication, bbox, crs, ):
    max_bbox = crs_def.CRSDefinitions[crs].max_bbox if crs else None
    cropped_bbox = (
        min(max(bbox[0], max_bbox[0]), max_bbox[2]),
        min(max(bbox[1], max_bbox[1]), max_bbox[3]),
        max(min(bbox[2], max_bbox[2]), max_bbox[0]),
        max(min(bbox[3], max_bbox[3]), max_bbox[1]),
    ) if not bbox_util.is_empty(bbox) and max_bbox else bbox
    srid = db_util.get_internal_srid(crs)
    query = f'''update {DB_SCHEMA}.publications set
    bbox = ST_MakeBox2D(ST_Point(%s, %s), ST_Point(%s ,%s)),
    srid = %s
    where type = %s
      and name = %s
      and id_workspace = (select w.id from {DB_SCHEMA}.workspaces w where w.name = %s);'''
    params = cropped_bbox + (srid, publication_type, publication, workspace,)
    db_util.run_statement(query, params)


def set_geodata_type(workspace, publication_type, publication, geodata_type, ):
    query = f'''update {DB_SCHEMA}.publications set
    geodata_type = %s
    where type = %s
      and name = %s
      and id_workspace = (select w.id from {DB_SCHEMA}.workspaces w where w.name = %s);'''
    params = (geodata_type, publication_type, publication, workspace,)
    db_util.run_statement(query, params)


def get_bbox_sphere_size(workspace, publication_type, publication):
    query = f"""
    select
        ST_DistanceSphere(
            st_transform(st_setsrid(ST_MakePoint(
                ST_XMin(bbox),
                (ST_YMax(bbox) + ST_YMin(bbox)) / 2
            ), srid), 4326),
            st_transform(st_setsrid(ST_MakePoint(
                ST_XMax(bbox),
                (ST_YMax(bbox) + ST_YMin(bbox)) / 2
            ), srid), 4326)
        ) as x_size,
        ST_DistanceSphere(
            st_transform(st_setsrid(ST_MakePoint(
                    ST_YMin(bbox),
                    (ST_XMax(bbox) + ST_XMin(bbox)) / 2
            ), srid), 4326),
            st_transform(st_setsrid(ST_MakePoint(
                ST_YMax(bbox),
                (ST_XMax(bbox) + ST_XMin(bbox)) / 2
            ), srid), 4326)
        ) as y_size
    from {DB_SCHEMA}.publications
    where type = %s
      and name = %s
      and id_workspace = (select w.id from {DB_SCHEMA}.workspaces w where w.name = %s)
        """

    [x_size, y_size] = db_util.run_query(query, (publication_type, publication, workspace))[0]
    return [x_size, y_size]


def set_wfs_wms_status(workspace, publication_type, publication, status, ):
    query = f'''update {DB_SCHEMA}.publications set
    wfs_wms_status = %s
    where type = %s
      and name = %s
      and id_workspace = (select w.id from {DB_SCHEMA}.workspaces w where w.name = %s);'''
    params = (status.value, publication_type, publication, workspace,)
    db_util.run_statement(query, params)
