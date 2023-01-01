from db import util as db_util


def run_query(query, data=None, conn_cur=None, encapsulate_exception=True, log_query=False):
    db_util.run_query(query=query, data=data, conn_cur=conn_cur, encapsulate_exception=encapsulate_exception,
                      log_query=log_query)


def run_statement(query, data=None, conn_cur=None, encapsulate_exception=True, log_query=False):
    db_util.run_statement(query=query, data=data, conn_cur=conn_cur,
                          encapsulate_exception=encapsulate_exception,
                          log_query=log_query)
