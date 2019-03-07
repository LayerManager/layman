from . import get_connection_cursor
from layman.settings import LAYMAN_PG_USER
from layman.http import LaymanError


def update_layer(username, layername, layerinfo):
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
	AND tableowner = '{LAYMAN_PG_USER}'
""")
    except:
        raise LaymanError(7)
    rows = cur.fetchall()
    if len(rows) > 0:
        return {
            'db_table': layername
        }
    else:
        return {}


def get_layer_names(username, conn_cur=None):
    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur
    try:
        cur.execute(f"""
    SELECT tablename
    FROM pg_tables
    WHERE schemaname = '{username}'
    	AND tableowner = '{LAYMAN_PG_USER}'
    """)
    except:
        raise LaymanError(7)
    rows = cur.fetchall()
    layer_names = list(map(lambda row: row[0], rows))
    return layer_names


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
    except:
        raise LaymanError(7)
