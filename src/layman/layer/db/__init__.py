import os
import psycopg2
from flask import g

from layman.http import LaymanError
from layman import settings


def create_connection_cursor():
    try:
        connection = psycopg2.connect(settings.PG_CONN)
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
    if username in settings.PG_NON_USER_SCHEMAS:
        raise LaymanError(8, {'schema': username})

    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur

    try:
        cur.execute(f"""select catalog_name, schema_name, schema_owner
    from information_schema.schemata
    where schema_owner <> '{settings.LAYMAN_PG_USER}' and schema_name = '{username}'""")
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
        cur.execute(
            f"""CREATE SCHEMA IF NOT EXISTS "{username}" AUTHORIZATION {settings.LAYMAN_PG_USER}""")
        conn.commit()
    except:
        raise LaymanError(7)


# def import_layer_vector_file(username, layername, main):
def import_layer_vector_file(username, layername, main_filepath, crs_id):
    p = import_layer_vector_file_async(username, layername, main_filepath,
                                    crs_id)
    while p.poll() is None:
        pass
    return_code = p.poll()
    if return_code != 0:
        raise LaymanError(11)


def import_layer_vector_file_async(username, layername, main_filepath,
                                    crs_id):
    # import file to database table
    import subprocess
    bash_args = [
        'ogr2ogr',
        '-t_srs', 'EPSG:3857',
        '-nln', layername,
        '--config', 'OGR_ENABLE_PARTIAL_REPROJECTION', 'TRUE',
        '-lco', f'SCHEMA={username}',
        # '-clipsrc', '-180', '-85.06', '180', '85.06',
        '-f', 'PostgreSQL',
        f'PG:{settings.PG_CONN}',
        # 'PG:{} active_schema={}'.format(PG_CONN, username),
    ]
    if crs_id is not None:
        bash_args.extend([
            '-s_srs', crs_id,
        ])
    if os.path.splitext(main_filepath)[1] == '.shp':
        bash_args.extend([
            '-nlt', 'PROMOTE_TO_MULTI',
            '-lco', 'PRECISION=NO',
        ])
    bash_args.extend([
        f'{main_filepath}',
    ])

    # print(' '.join(bash_args))
    p = subprocess.Popen(bash_args, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    return p


def check_new_layername(username, layername, conn_cur=None):
    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur

    # DB table name conflicts
    try:
        cur.execute(f"""SELECT n.nspname AS schemaname, c.relname, c.relkind
    FROM   pg_class c
    JOIN   pg_namespace n ON n.oid = c.relnamespace
    WHERE  n.nspname IN ('{username}', '{settings.PG_POSTGIS_SCHEMA}') AND c.relname='{layername}'""")
    except:
        raise LaymanError(7)
    rows = cur.fetchall()
    if len(rows) > 0:
        raise LaymanError(9, {'db_object_name': layername})
