from db import util as db_util
from layman import settings, patch_mode, util as layman_util
from layman.common import empty_method, empty_method_returns_none, empty_method_returns_dict
from layman.http import LaymanError
from . import get_table_name
from .. import LAYER_TYPE

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


pre_publication_action_check = empty_method
post_layer = empty_method
patch_layer = empty_method
get_metadata_comparison = empty_method_returns_dict
get_publication_uuid = empty_method_returns_none


def get_layer_info(workspace, layername, conn_cur=None):
    table_name = get_table_name(workspace, layername)
    result = {}
    if table_name:
        if conn_cur is None:
            pg_conn = layman_util.get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': ['db_connection_string', ]})[
                '_db_connection_string']
            conn_cur = db_util.get_connection_cursor(pg_conn)
        _, cur = conn_cur
        try:
            cur.execute(f"""
    SELECT schemaname, tablename, tableowner
    FROM pg_tables
    WHERE schemaname = '{workspace}'
        AND tablename = '{table_name}'
        AND tableowner = '{settings.LAYMAN_PG_USER}'
    """)
        except BaseException as exc:
            raise LaymanError(7) from exc
        rows = cur.fetchall()
        if len(rows) > 0:
            result = {
                'db_table': {
                    'name': table_name,
                },
            }
    return result


def delete_layer(workspace, layername):
    pg_conn = layman_util.get_publication_info(workspace, LAYER_TYPE, layername, context={'keys': ['db_connection_string', ]})['_db_connection_string']
    conn, cur = db_util.get_connection_cursor(pg_conn)
    table_name = get_table_name(workspace, layername)
    query = f"""
    DROP TABLE IF EXISTS "{workspace}"."{table_name}" CASCADE
    """
    try:
        cur.execute(query)
        conn.commit()
    except BaseException as exc:
        raise LaymanError(7)from exc


def set_layer_srid(schema, layername, table_name, srid):
    pg_conn = layman_util.get_publication_info(schema, LAYER_TYPE, layername, context={'keys': ['db_connection_string', ]})['_db_connection_string']
    conn_cur = db_util.get_connection_cursor(pg_conn)
    query = '''SELECT UpdateGeometrySRID(%s, %s, 'wkb_geometry', %s);'''
    params = (schema, table_name, srid)
    db_util.run_query(query, params, conn_cur=conn_cur)
