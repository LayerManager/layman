import os
import sys
import time

ATTEMPT_INTERVAL = 2
MAX_ATTEMPTS = 60


PG_HOST = os.environ['PG_HOST']
PG_PORT = os.environ['PG_PORT']
PG_DBNAME = os.environ['PG_DBNAME']
PG_USER = os.environ['PG_USER']
PG_PASSWORD = os.environ['PG_PASSWORD']
PG_CONN = {
    'host': PG_HOST,
    'port': PG_PORT,
    'dbname': PG_DBNAME,
    'user': PG_USER,
    'password': PG_PASSWORD,
}
PG_TEMPLATE_DBNAME = os.environ['PG_TEMPLATE_DBNAME']
INIT_SQL_FILE_PATHS = os.environ['INIT_SQL_FILE_PATHS'].split(',')



def main():

    attempt = 1

    # PostgreSQL (try to connect to default 'postgres' database
    pg_conn_dict = PG_CONN.copy()
    pg_conn_dict['dbname'] = 'postgres'
    secret_conn_dict = {k: v for k, v in pg_conn_dict.items() if k != 'password'}
    wait_for_msg = f"PostgreSQL database, {secret_conn_dict}"
    print(f"Waiting for {wait_for_msg}")
    while True:
        import psycopg2
        try:
            with psycopg2.connect(**pg_conn_dict) as conn:
                pass
            print(f"Attempt {attempt}/{MAX_ATTEMPTS} successful.")
            break
        except psycopg2.OperationalError as e:
            handle_exception(e, attempt, wait_for_msg)
            attempt += 1
    print()



    micka_conn_dict = PG_CONN.copy()
    dbname = micka_conn_dict['dbname']
    print(f"Checking existence of {dbname} database")

    try:
        with psycopg2.connect(**micka_conn_dict):
            pass
        print(f"Database {dbname} exists.")
    except psycopg2.OperationalError as e:
        print(f"Database {dbname} does not exist, creating")
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        with psycopg2.connect(**pg_conn_dict) as pg_conn:
            pg_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = pg_conn.cursor()
            cur.execute(f"CREATE DATABASE {dbname} WITH TEMPLATE={PG_TEMPLATE_DBNAME} ENCODING='UTF8' CONNECTION LIMIT=-1;")
            cur.close()
        print(f"Database {dbname} created")
        with psycopg2.connect(**micka_conn_dict) as micka_conn:
            cur = micka_conn.cursor()
            for init_sql_file_path in INIT_SQL_FILE_PATHS:
                print(f"Running SQL file {init_sql_file_path}")
                cur.execute(open(init_sql_file_path, "r", encoding="utf-8").read())
            cur.close()


def handle_exception(e, attempt, wait_for_msg=None):
    if attempt < MAX_ATTEMPTS:
        msg_end = f"Waiting {ATTEMPT_INTERVAL} seconds before next attempt."
    else:
        msg_end = "Max attempts reached!"
    # print(f"Attempt {attempt}/{MAX_ATTEMPTS} failed:")
    # print(e)
    # print(msg_end)
    # traceback.print_exc()
    if attempt >= MAX_ATTEMPTS:
        print(f"Reaching max attempts when waiting for {wait_for_msg}")
        sys.exit(1)
        # raise e
    time.sleep(ATTEMPT_INTERVAL)


if __name__ == "__main__":
    main()
