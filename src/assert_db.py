import importlib
import os
import re
import shutil
import sys
import time
from urllib.parse import urljoin

settings = importlib.import_module(os.environ['LAYMAN_SETTINGS_MODULE'])

ATTEMPT_INTERVAL = 1
MAX_ATTEMPTS = 10


def main():
    attempt = 1

    print(f"Assertting DB.")
    # postgresql
    conn_dict = settings.PG_CONN.copy()
    conn_dict['dbname'] = 'postgres'
    secret_conn_dict = {k: v for k, v in conn_dict.items() if k != 'password'}
    wait_for_msg = f"PostgreSQL database, {secret_conn_dict}"
    print(f"Waiting for {wait_for_msg}")
    while True:
        import psycopg2
        try:
            with psycopg2.connect(**conn_dict):
                pass
            print(f"Attempt {attempt}/{MAX_ATTEMPTS} successful.")
            break
        except psycopg2.OperationalError as e:
            handle_exception(e, attempt, wait_for_msg)
            attempt += 1

    try:
        conn_dict = settings.PG_CONN.copy()
        secret_conn_dict = {k: v for k, v in conn_dict.items() if k != 'password'}
        print(f"Trying to connect to DB {secret_conn_dict}")
        with psycopg2.connect(**conn_dict):
            pass
        print(f"DB {conn_dict['dbname']} exists.")
    except BaseException:
        print(f"DB {conn_dict['dbname']} does not exists, creating.")
        conn_dict = settings.PG_CONN.copy()
        conn_dict['dbname'] = 'postgres'
        conn = psycopg2.connect(**conn_dict)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            f"""CREATE DATABASE {settings.LAYMAN_PG_DBNAME} TEMPLATE {settings.LAYMAN_PG_TEMPLATE_DBNAME}""")
        conn.close()
        print(f"DB {conn_dict['dbname']} created.")


def handle_exception(e, attempt, wait_for_msg=None):
    if attempt >= MAX_ATTEMPTS:
        print(f"Reaching max attempts when waiting for {wait_for_msg}")
        sys.exit(1)
        # raise e
    time.sleep(ATTEMPT_INTERVAL)


if __name__ == "__main__":
    main()
