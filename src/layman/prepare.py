import os
import shutil
import pathlib
from settings import *

def main():
    if TESTING:
        if os.path.exists(LAYMAN_DATA_PATH):
            shutil.rmtree(LAYMAN_DATA_PATH)
    pathlib.Path(LAYMAN_DATA_PATH).mkdir(exist_ok=True)

    if TESTING:
        import psycopg2
        conn = psycopg2.connect(PG_CONN_TEMPLATE)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("""
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '{}'
  AND pid <> pg_backend_pid();
""".format(LAYMAN_PG_DBNAME))
        cur.execute("""DROP DATABASE IF EXISTS {}""".format(LAYMAN_PG_DBNAME))
        cur.execute("""CREATE DATABASE {} TEMPLATE {}""".format(
            LAYMAN_PG_DBNAME, LAYMAN_PG_TEMPLATE_DBNAME))
        conn.close()

if __name__ == "__main__":
    main()