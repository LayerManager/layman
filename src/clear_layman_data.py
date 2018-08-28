import shutil
import re
from layman.settings import *
from layman.geoserver import get_layman_rules
from urllib.parse import urljoin


def main():
    if os.path.exists(LAYMAN_DATA_PATH):
        shutil.rmtree(LAYMAN_DATA_PATH)

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
            cur.execute("""DROP SCHEMA "{}" CASCADE""".format(row[1]))
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

    import requests
    headers_json = {
        'Accept': 'application/json',
        'Content-type': 'application/json',
    }
    r = requests.get(
        LAYMAN_GS_REST_SECURITY_ACL_LAYERS,
        headers=headers_json,
        auth=LAYMAN_GS_AUTH
    )
    r.raise_for_status()
    all_rules = r.json()
    layman_rules = get_layman_rules(all_rules)
    for rule in layman_rules:
        workspace = re.match(r"^([^.]+)\..*", rule).group(1)
        r = requests.delete(
            urljoin(LAYMAN_GS_REST_WORKSPACES, workspace),
            headers=headers_json,
            auth=LAYMAN_GS_AUTH,
            params={
                'recurse': 'true'
            }
        )
        r.raise_for_status()
        r = requests.delete(
            urljoin(LAYMAN_GS_REST_SECURITY_ACL_LAYERS, rule),
            headers=headers_json,
            auth=LAYMAN_GS_AUTH,
        )
        r.raise_for_status()


if __name__ == "__main__":
    main()