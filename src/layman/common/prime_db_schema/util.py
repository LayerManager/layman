from db import util as db_util
from layman import settings


def run_query(query, data=None, conn_cur=None, encapsulate_exception=True, log_query=False):
    db_util.run_query(query=query, data=data, pg_conn=settings.PG_CONN, conn_cur=conn_cur, encapsulate_exception=encapsulate_exception,
                      log_query=log_query)


def run_statement(query, data=None, conn_cur=None, encapsulate_exception=True, log_query=False):
    db_util.run_statement(query=query, data=data, pg_conn=settings.PG_CONN, conn_cur=conn_cur,
                          encapsulate_exception=encapsulate_exception,
                          log_query=log_query)
