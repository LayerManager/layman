import psycopg2

from .http import LaymanError
from .settings import *

CONNECTION = None
CURSOR = None

def create_connection_cursor():
    try:
        connection = psycopg2.connect(PG_CONN)
    except:
        raise LaymanError(6)
    cursor = connection.cursor()
    return (connection, cursor)

def get_connection_cursor():
    global CURSOR, CONNECTION
    if CURSOR is None or CONNECTION is None:
        CONNECTION, CURSOR = create_connection_cursor()
    return CONNECTION, CURSOR


def ensure_user_schema(username, conn_cur=None):
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