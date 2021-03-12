from flask import g, current_app as app
import psycopg2
import re

from layman import settings
from layman.http import LaymanError


FLASK_CONN_CUR_KEY = f'{__name__}:CONN_CUR'


def create_connection_cursor():
    try:
        connection = psycopg2.connect(**settings.PG_CONN)
        connection.set_session(autocommit=True)
    except BaseException:
        raise LaymanError(6)
    cursor = connection.cursor()
    return connection, cursor


def get_connection_cursor():
    key = FLASK_CONN_CUR_KEY
    if key not in g:
        conn_cur = create_connection_cursor()
        g.setdefault(key, conn_cur)
    return g.get(key)


def run_query(query, data=None, conn_cur=None, encapsulate_exception=True):
    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur
    try:
        cur.execute(query, data)
        rows = cur.fetchall()
        conn.commit()
    except BaseException as exc:
        if encapsulate_exception:
            app.logger.error(f"run_query, query={query}, data={data}, exc={exc}")
            raise LaymanError(7)
        else:
            raise exc

    return rows


def run_statement(query, data=None, conn_cur=None, encapsulate_exception=True):
    if conn_cur is None:
        conn_cur = get_connection_cursor()
    conn, cur = conn_cur
    try:
        cur.execute(query, data)
        rows = cur.rowcount
        conn.commit()
    except BaseException as exc:
        if encapsulate_exception:
            app.logger.error(f"run_query, query={query}, data={data}, exc={exc}")
            raise LaymanError(7)
        else:
            raise exc
    return rows


def to_tsquery_string(value):
    value = re.sub(r'[\W_]+', ' ', value, flags=re.UNICODE).strip()
    value = value.replace(' ', ' | ')
    return value
