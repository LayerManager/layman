import psycopg2

from flask import g, current_app

from .http import LaymanError
from .settings import *


def create_connection_cursor():
    try:
        connection = psycopg2.connect(PG_CONN)
    except:
        raise LaymanError(6)
    cursor = connection.cursor()
    return (connection, cursor)

def get_connection_cursor():
    key = 'layman.postgresql.conn_cur'
    if key not in g:
        conn_cur = create_connection_cursor()
        g.setdefault(key, conn_cur)
    return g.get(key)


def check_username(username, conn_cur=None):
    if username in PG_NON_USER_SCHEMAS:
        raise LaymanError(8, {'schema': username})

    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur

    try:
        cur.execute("""select catalog_name, schema_name, schema_owner
    from information_schema.schemata
    where schema_owner <> '{}' and schema_name = '{}'""".format(
            LAYMAN_PG_USER, username))
    except:
        raise LaymanError(7)
    rows = cur.fetchall()
    if len(rows) > 0:
        raise LaymanError(10, {'schema': username})


def ensure_user_schema(username, conn_cur=None):
    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur

    try:
        cur.execute("""CREATE SCHEMA IF NOT EXISTS "{}" AUTHORIZATION {}""".format(
        username, LAYMAN_PG_USER))
        conn.commit()
    except:
        raise LaymanError(7)


# def import_layer_vector_file(username, layername, main):
def import_layer_vector_file(username, layername, main_filepath, crs_id,
                             conn_cur=None):
    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur
    # DB table name conflicts
    try:
        cur.execute("""SELECT n.nspname AS schemaname, c.relname, c.relkind
FROM   pg_class c
JOIN   pg_namespace n ON n.oid = c.relnamespace
WHERE  n.nspname IN ('{}', '{}') AND c.relname='{}'""".format(
            username, PG_POSTGIS_SCHEMA, layername))
    except:
        raise LaymanError(7)
    rows = cur.fetchall()
    if len(rows) > 0:
        raise LaymanError(9, {'db_object_name': layername})

    # import file to database table
    import subprocess
    bash_args = [
        'ogr2ogr',
        '-t_srs', 'EPSG:3857',
        '-nln', layername,
        '--config', 'OGR_ENABLE_PARTIAL_REPROJECTION', 'TRUE',
        '-lco', 'SCHEMA={}'.format(username),
        # '-clipsrc', '-180', '-85.06', '180', '85.06',
        '-f', 'PostgreSQL',
        'PG:{}'.format(PG_CONN),
        # 'PG:{} active_schema={}'.format(PG_CONN, username),
    ]
    if crs_id is not None:
        bash_args.extend([
            '-s_srs', crs_id,
        ])
    bash_args.extend([
        '{}'.format(main_filepath),
    ])

    # app.logger.info(' '.join(bash_args))
    return_code = subprocess.call(bash_args)
    if return_code != 0:
        raise LaymanError(11)

def get_layer_info(username, layername, conn_cur=None):
    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur
    try:
        cur.execute("""
SELECT schemaname, tablename, tableowner
FROM pg_tables
WHERE schemaname = '{}'
	AND tablename = '{}'
	AND tableowner = '{}'
""".format(username, layername, LAYMAN_PG_USER))
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
        cur.execute("""
    SELECT tablename
    FROM pg_tables
    WHERE schemaname = '{}'
    	AND tableowner = '{}'
    """.format(username, LAYMAN_PG_USER))
    except:
        raise LaymanError(7)
    rows = cur.fetchall()
    layer_names = list(map(lambda row: row[0], rows))
    return layer_names