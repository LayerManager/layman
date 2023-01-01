from layman import settings
from layman.common import empty_method
from . import util as db_util

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA

check_workspace_name = empty_method


def ensure_workspace(name):
    workspaces = get_workspace_infos(name)
    if workspaces:
        result = workspaces[name]["id"]
    else:
        sql = f"""insert into {DB_SCHEMA}.workspaces (name)
        values (%s)
        ON CONFLICT (name) DO update SET name = EXCLUDED.name returning id;"""
        data = (name, )
        ids = db_util.run_query(sql, data)
        result = ids[0][0]
    return result


def delete_workspace(name):
    sql = f"delete from {DB_SCHEMA}.workspaces where name = %s;"
    db_util.run_statement(sql, (name,))


def get_workspace_infos(name=None):
    sql = f"""with const as (select %s as name)
    select w.id,
           w.name
    from {DB_SCHEMA}.workspaces w inner join
         const c on (   c.name = w.name
                     or c.name is null)
    order by w.name asc
    ;"""
    values = db_util.run_query(sql, (name,))
    result = {name: {"id": workspace_id,
                     "name": name,
                     } for workspace_id, name in
              values}
    return result


def get_workspace_names():
    return get_workspace_infos().keys()
