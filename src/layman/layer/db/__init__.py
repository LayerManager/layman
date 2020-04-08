from collections import defaultdict
import os
import psycopg2
from flask import g

from layman.common.language import get_languages_iso639_2
from layman.http import LaymanError
from layman import settings


FLASK_CONN_CUR_KEY = f'{__name__}:CONN_CUR'


def create_connection_cursor():
    try:
        connection = psycopg2.connect(**settings.PG_CONN)
    except:
        raise LaymanError(6)
    cursor = connection.cursor()
    return (connection, cursor)

def get_connection_cursor():
    key = FLASK_CONN_CUR_KEY
    if key not in g:
        conn_cur = create_connection_cursor()
        g.setdefault(key, conn_cur)
    return g.get(key)


def get_usernames(conn_cur=None):
    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur

    try:
        cur.execute(f"""select schema_name
    from information_schema.schemata
    where schema_name NOT IN ('{"', '".join(settings.PG_NON_USER_SCHEMAS)}') AND schema_owner = '{settings.LAYMAN_PG_USER}'""")
    except:
        raise LaymanError(7)
    rows = cur.fetchall()
    return [
        r[0] for r in rows
    ]



def check_username(username, conn_cur=None):
    if username in settings.PG_NON_USER_SCHEMAS:
        raise LaymanError(35, {'reserved_by': __name__, 'schema': username})

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
        raise LaymanError(35, {'reserved_by': __name__, 'schema': username, 'reason': 'DB schema owned by another than layman user'})


def ensure_user_workspace(username, conn_cur=None):
    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur

    try:
        cur.execute(
            f"""CREATE SCHEMA IF NOT EXISTS "{username}" AUTHORIZATION {settings.LAYMAN_PG_USER}""")
        conn.commit()
    except:
        raise LaymanError(7)


def delete_user_workspace(username, conn_cur=None):
    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur

    try:
        cur.execute(
            f"""DROP SCHEMA IF EXISTS "{username}" RESTRICT""")
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
        pg_error = str(p.stdout.read())
        raise LaymanError(11, private_data=pg_error)


def import_layer_vector_file_async(username, layername, main_filepath,
                                    crs_id):
    # import file to database table
    import subprocess
    pg_conn = ' '.join([f"{k}='{v}'" for k, v in settings.PG_CONN.items()])
    bash_args = [
        'ogr2ogr',
        '-t_srs', 'EPSG:3857',
        '-nln', layername,
        '--config', 'OGR_ENABLE_PARTIAL_REPROJECTION', 'TRUE',
        '-lco', f'SCHEMA={username}',
        # '-clipsrc', '-180', '-85.06', '180', '85.06',
        '-f', 'PostgreSQL',
        f'PG:{pg_conn}',
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


def get_text_column_names(username, layername, conn_cur=None):
    conn, cur = conn_cur or get_connection_cursor()

    try:
        cur.execute(f"""
SELECT QUOTE_IDENT(column_name) AS column_name
FROM information_schema.columns 
WHERE table_schema = '{username}' 
AND table_name = '{layername}'
AND data_type IN ('character varying', 'varchar', 'character', 'char', 'text')
""")
    except:
        raise LaymanError(7)
    rows = cur.fetchall()
    return [r[0] for r in rows]


def get_text_data(username, layername, conn_cur=None):
    conn, cur = conn_cur or get_connection_cursor()
    col_names = get_text_column_names(username, layername, conn_cur=conn_cur)
    if len(col_names) == 0:
        return None
    try:
        cur.execute(f"""
select {', '.join(col_names)}
from {username}.{layername}
order by ogc_fid
limit 100
""")
    except:
        raise LaymanError(7)
    rows = cur.fetchall()
    col_texts = defaultdict(list)
    for row in rows:
        for idx in range(len(col_names)):
            col_name = col_names[idx]
            v = row[idx]
            if v is not None and len(v)>0:
                col_texts[col_name].append(v)
    col_texts = [
        ' '.join(texts)
        for _, texts in col_texts.items()
    ]
    # print(f"result col_texts={col_texts}")
    return col_texts


def get_text_languages(username, layername):
    texts = get_text_data(username, layername)
    all_langs = set()
    for t in texts:
        # skip short texts
        if len(t) < 100:
            continue
        langs = get_languages_iso639_2(t)
        if len(langs):
            lang = langs[0]
            # print(f"text={t}\nlanguage={lang}")
            all_langs.add(lang)
    return sorted(list(all_langs))
