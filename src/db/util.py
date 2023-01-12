import logging
import re
import psycopg2
from flask import g

import crs as crs_def
from . import PG_CONN
from .error import Error

logger = logging.getLogger(__name__)

FLASK_CONN_CUR_KEY = f'{__name__}:CONN_CUR'


def create_connection_cursor(uri=None, encapsulate_exception=True):
    try:
        connection = psycopg2.connect(uri) if uri else psycopg2.connect(**PG_CONN)
        connection.set_session(autocommit=True)
    except BaseException as exc:
        if encapsulate_exception:
            raise Error(1) from exc
        raise exc
    cursor = connection.cursor()
    return connection, cursor


def get_connection_cursor():
    key = FLASK_CONN_CUR_KEY
    if key not in g:
        conn_cur = create_connection_cursor()
        g.setdefault(key, conn_cur)
    return g.get(key)


def run_query(query, data=None, conn_cur=None, encapsulate_exception=True, log_query=False):
    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur
    try:
        if log_query:
            logger.info(f"query={cur.mogrify(query, data).decode()}")
        cur.execute(query, data)
        rows = cur.fetchall()
        conn.commit()
    except BaseException as exc:
        if encapsulate_exception:
            logger.error(f"run_query, query={query}, data={data}, exc={exc}")
            raise Error(2) from exc
        raise exc

    return rows


def run_statement(query, data=None, conn_cur=None, encapsulate_exception=True, log_query=False):
    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur
    try:
        if log_query:
            logger.info(f"query={cur.mogrify(query, data).decode()}")
        cur.execute(query, data)
        rows = cur.rowcount
        conn.commit()
    except BaseException as exc:
        if encapsulate_exception:
            logger.error(f"run_query, query={query}, data={data}, exc={exc}")
            raise Error(2) from exc
        raise exc
    return rows


def to_tsquery_string(value):
    value = re.sub(r'[\W_]+', ' ', value, flags=re.UNICODE).strip()
    value = value.replace(' ', ' | ')
    return value


def get_srid(crs):
    if crs is None:
        srid = None
    else:
        srid = crs_def.CRSDefinitions[crs].srid
        if not srid:
            auth_name, auth_srid = crs.split(':')
            auth_srid = int(auth_srid)
            sql = 'select srid from spatial_ref_sys where auth_name = %s and auth_srid = %s;'
            srid = run_query(sql, (auth_name, auth_srid, ))[0][0]
    return srid


def get_crs(srid):
    crs = next((
        crs_code for crs_code, crs_item_def in crs_def.CRSDefinitions.items()
        if crs_item_def.srid == srid
    ), None)
    if not crs:
        sql = 'select auth_name, auth_srid from spatial_ref_sys where srid = %s;'
        auth_name, auth_srid = run_query(sql, (srid, ))[0]
        if auth_name or auth_srid:
            crs = f'{auth_name}:{auth_srid}'
    return crs


def ensure_srid_definition(srid, proj4text):
    sql = f'''INSERT into spatial_ref_sys (srid, auth_name, auth_srid, proj4text, srtext) values ( %s, null, null, %s, null)
ON CONFLICT (srid) DO UPDATE SET proj4text = %s;'''
    params = (srid, proj4text, proj4text)
    run_statement(sql, params)
