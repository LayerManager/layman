import logging
import re
from urllib import parse
import psycopg2
import psycopg2.pool

import crs as crs_def
from . import PG_URI_STR
from .error import Error

logger = logging.getLogger(__name__)

CONNECTION_POOL_DICT = {}


def get_connection_pool(db_uri_str=None, encapsulate_exception=True):
    db_uri_str = db_uri_str or PG_URI_STR
    connection_pool = CONNECTION_POOL_DICT.get(db_uri_str)
    if not connection_pool:
        db_uri_parsed = parse.urlparse(db_uri_str)
        try:
            connection_pool = psycopg2.pool.ThreadedConnectionPool(3, 20,
                                                                   user=db_uri_parsed.username,
                                                                   password=db_uri_parsed.password,
                                                                   host=db_uri_parsed.hostname,
                                                                   port=db_uri_parsed.port,
                                                                   database=db_uri_parsed.path[1:],
                                                                   )
        except BaseException as exc:
            if encapsulate_exception:
                raise Error(1) from exc
            raise exc
        CONNECTION_POOL_DICT[db_uri_str] = connection_pool
    return connection_pool


def run_query(query, data=None, uri_str=None, encapsulate_exception=True, log_query=False):
    pool = get_connection_pool(db_uri_str=uri_str, encapsulate_exception=encapsulate_exception, )
    conn = pool.getconn()
    conn.autocommit = True
    cur = conn.cursor()
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
    finally:
        pool.putconn(conn)

    return rows


def run_statement(query, data=None, uri_str=None, encapsulate_exception=True, log_query=False):
    pool = get_connection_pool(db_uri_str=uri_str, encapsulate_exception=encapsulate_exception, )
    conn = pool.getconn()
    conn.autocommit = True
    cur = conn.cursor()
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
    finally:
        pool.putconn(conn)

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


def get_crs_from_srid(srid, uri_str=None, *, use_internal_srid):
    crs = next((
        crs_code for crs_code, crs_item_def in crs_def.CRSDefinitions.items()
        if crs_item_def.internal_srid == srid
    ), None) if use_internal_srid else None
    if not crs:
        sql = 'select auth_name, auth_srid from spatial_ref_sys where srid = %s;'
        auth_name, auth_srid = run_query(sql, (srid, ), uri_str=uri_str)[0]
        if auth_name or auth_srid:
            crs = f'{auth_name}:{auth_srid}'
    return crs


def ensure_srid_definition(srid, proj4text):
    sql = f'''INSERT into spatial_ref_sys (srid, auth_name, auth_srid, proj4text, srtext) values ( %s, null, null, %s, null)
ON CONFLICT (srid) DO UPDATE SET proj4text = %s;'''
    params = (srid, proj4text, proj4text)
    run_statement(sql, params)
