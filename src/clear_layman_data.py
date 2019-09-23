import importlib
import os
import re
import shutil
from urllib.parse import urljoin


settings = importlib.import_module(os.environ['LAYMAN_SETTINGS_MODULE'])


def main():
    if os.path.exists(settings.LAYMAN_DATA_DIR):
        for the_file in os.listdir(settings.LAYMAN_DATA_DIR):
            file_path = os.path.join(settings.LAYMAN_DATA_DIR, the_file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

    import psycopg2
    try:
        conn = psycopg2.connect(**settings.PG_CONN)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f"""
select catalog_name, schema_name, schema_owner
from information_schema.schemata
where schema_owner = '{settings.LAYMAN_PG_USER}'
    and schema_name NOT IN ({', '.join(map(lambda s: "'" + s + "'", settings.PG_NON_USER_SCHEMAS))})
""")
        rows = cur.fetchall()
        for row in rows:
            cur.execute(f"""DROP SCHEMA "{row[1]}" CASCADE""")
        conn.close()
    except:
        conn = psycopg2.connect(**settings.PG_CONN_TEMPLATE)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f"""
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '{settings.LAYMAN_PG_TEMPLATE_DBNAME}'
AND pid <> pg_backend_pid();
""")
        cur.execute(
            f"""CREATE DATABASE {settings.LAYMAN_PG_DBNAME} TEMPLATE {settings.LAYMAN_PG_TEMPLATE_DBNAME}""")
        conn.close()


    settings.LAYMAN_REDIS.flushdb()


    import requests
    headers_json = {
        'Accept': 'application/json',
        'Content-type': 'application/json',
    }
    r = requests.get(
        settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS,
        headers=headers_json,
        auth=settings.LAYMAN_GS_AUTH
    )
    r.raise_for_status()
    all_rules = r.json()

    def get_role_rules(all_rules, role):
        re_role = r".*\b" + re.escape(role) + r"\b.*"
        result = {k: v for k, v in all_rules.items() if re.match(re_role, v)}
        return result

    layman_rules = get_role_rules(all_rules, settings.LAYMAN_GS_ROLE)
    for rule in layman_rules:
        workspace = re.match(r"^([^.]+)\..*", rule).group(1)
        r = requests.delete(
            urljoin(settings.LAYMAN_GS_REST_WORKSPACES, workspace),
            headers=headers_json,
            auth=settings.LAYMAN_GS_AUTH,
            params={
                'recurse': 'true'
            }
        )
        r.raise_for_status()
        r = requests.delete(
            urljoin(settings.LAYMAN_GS_REST_SECURITY_ACL_LAYERS, rule),
            headers=headers_json,
            auth=settings.LAYMAN_GS_AUTH,
        )
        r.raise_for_status()


if __name__ == "__main__":
    main()
