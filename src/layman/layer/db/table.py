from db import util as db_util
from layman import settings, patch_mode
from layman.common import empty_method, empty_method_returns_none, empty_method_returns_dict
from layman.http import LaymanError

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


pre_publication_action_check = empty_method
post_layer = empty_method
patch_layer = empty_method
get_metadata_comparison = empty_method_returns_dict
get_publication_uuid = empty_method_returns_none


def get_layer_info(workspace, layername, conn_cur=None):
    if conn_cur is None:
        conn_cur = db_util.get_connection_cursor()
    _, cur = conn_cur
    try:
        cur.execute(f"""
SELECT schemaname, tablename, tableowner
FROM pg_tables
WHERE schemaname = '{workspace}'
    AND tablename = '{layername}'
    AND tableowner = '{settings.LAYMAN_PG_USER}'
""")
    except BaseException as exc:
        raise LaymanError(7) from exc
    rows = cur.fetchall()
    result = {}
    if len(rows) > 0:
        result = {
            'db_table': {
                'name': layername,
            },
        }
    return result


def delete_layer(workspace, layername, conn_cur=None):
    if conn_cur is None:
        conn_cur = db_util.get_connection_cursor()
    conn, cur = conn_cur
    query = f"""
    DROP TABLE IF EXISTS "{workspace}"."{layername}" CASCADE
    """
    try:
        cur.execute(query)
        conn.commit()
    except BaseException as exc:
        raise LaymanError(7)from exc
