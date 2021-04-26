import logging
import re
import psycopg2
from flask import g

from . import PG_CONN
from .error import Error

logger = logging.getLogger(__name__)

FLASK_CONN_CUR_KEY = f'{__name__}:CONN_CUR'


def create_connection_cursor():
    try:
        connection = psycopg2.connect(**PG_CONN)
        connection.set_session(autocommit=True)
    except BaseException as exc:
        raise Error(1) from exc
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
