import logging
import re
import psycopg2
from flask import g

import crs as crs_def
from . import PG_URI_STR
from .error import Error

logger = logging.getLogger(__name__)

FLASK_CONN_CUR_KEY = f'{__name__}:CONN_CUR'


def create_connection_cursor(db_uri_str=None, encapsulate_exception=True):
    db_uri_str = db_uri_str or PG_URI_STR
    try:
        connection = psycopg2.connect(db_uri_str)
        connection.set_session(autocommit=True)
    except BaseException as exc:
        if encapsulate_exception:
            raise Error(1) from exc
        raise exc
    cursor = connection.cursor()
    return connection, cursor


def get_connection_cursor(db_uri_str=None, encapsulate_exception=True):
    if db_uri_str is None or db_uri_str == PG_URI_STR:
        key = FLASK_CONN_CUR_KEY
        if key not in g:
            conn_cur = create_connection_cursor(encapsulate_exception=encapsulate_exception)
            g.setdefault(key, conn_cur)
        result = g.get(key)
    else:
        result = create_connection_cursor(db_uri_str=db_uri_str, encapsulate_exception=encapsulate_exception)
    return result


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


def get_internal_srid(crs):
    if crs is None:
        srid = None
    else:
        srid = crs_def.CRSDefinitions[crs].internal_srid
        if not srid:
            auth_name, auth_srid = crs.split(':')
            auth_srid = int(auth_srid)
            sql = 'select srid from spatial_ref_sys where auth_name = %s and auth_srid = %s;'
            srid = run_query(sql, (auth_name, auth_srid, ))[0][0]
    return srid


def get_crs_from_srid(srid, conn_cur=None, *, use_internal_srid):
    crs = next((
        crs_code for crs_code, crs_item_def in crs_def.CRSDefinitions.items()
        if crs_item_def.internal_srid == srid
    ), None) if use_internal_srid else None
    if not crs:
        sql = 'select auth_name, auth_srid from spatial_ref_sys where srid = %s;'
        auth_name, auth_srid = run_query(sql, (srid, ), conn_cur=conn_cur)[0]
        if auth_name or auth_srid:
            crs = f'{auth_name}:{auth_srid}'
    return crs


def ensure_srid_definition(srid, proj4text):
    sql = f'''INSERT into spatial_ref_sys (srid, auth_name, auth_srid, proj4text, srtext) values ( %s, null, null, %s, null)
ON CONFLICT (srid) DO UPDATE SET proj4text = %s;'''
    params = (srid, proj4text, proj4text)
    run_statement(sql, params)
