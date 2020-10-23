from . import get_connection_cursor
from layman import settings, patch_mode
from layman.http import LaymanError

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


def post_layer(username, layername):
    pass


def patch_layer(username, layername):
    pass


def get_layer_info(username, layername, conn_cur=None):
    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur
    try:
        cur.execute(f"""
SELECT schemaname, tablename, tableowner
FROM pg_tables
WHERE schemaname = '{username}'
    AND tablename = '{layername}'
    AND tableowner = '{settings.LAYMAN_PG_USER}'
""")
    except BaseException:
        raise LaymanError(7)
    rows = cur.fetchall()
    if len(rows) > 0:
        return {
            'db_table': layername
        }
    else:
        return {}


def get_layer_infos(username, conn_cur=None):
    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur
    try:
        cur.execute(f"""
    SELECT tablename
    FROM pg_tables
    WHERE schemaname = '{username}'
        AND tableowner = '{settings.LAYMAN_PG_USER}'
    """)
    except BaseException:
        raise LaymanError(7)
    rows = cur.fetchall()
    layer_infos = {}
    for row in rows:
        layer_infos[row[0]] = {"name": row[0]}
    return layer_infos


def delete_layer(username, layername, conn_cur=None):
    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur
    query = f"""
    DROP TABLE IF EXISTS "{username}"."{layername}" CASCADE
    """
    try:
        cur.execute(query)
        conn.commit()
    except BaseException:
        raise LaymanError(7)


def get_publication_infos(username, publication_type):
    if publication_type != '.'.join(__name__.split('.')[:-2]):
        raise Exception(f'Unknown pyblication type {publication_type}')

    infos = get_layer_infos(username)
    return infos


def get_publication_uuid(username, publication_type, publication_name):
    return None


def get_metadata_comparison(username, publication_name):
    pass
