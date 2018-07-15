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
        try:
            conn = psycopg2.connect(PG_CONN)
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute("""
select catalog_name, schema_name, schema_owner
from information_schema.schemata
where schema_owner = '{}' and schema_name NOT IN ({})""".format(
                LAYMAN_PG_USER,
                ', '.join(map(lambda s: "'" + s + "'", PG_NON_USER_SCHEMAS))))
            rows = cur.fetchall()
            for row in rows:
                cur.execute("""DROP SCHEMA {} CASCADE""".format(row[1]))
            conn.close()
        except:
            conn = psycopg2.connect(PG_CONN_TEMPLATE)
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute("""
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '{}'
  AND pid <> pg_backend_pid();
            """.format(LAYMAN_PG_TEMPLATE_DBNAME))
            cur.execute("""CREATE DATABASE {} TEMPLATE {}""".format(
                LAYMAN_PG_DBNAME, LAYMAN_PG_TEMPLATE_DBNAME))
            conn.close()

if __name__ == "__main__":
    main()