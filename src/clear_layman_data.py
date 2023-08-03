import os
import shutil
from urllib.parse import urljoin
import geoserver
import micka
import layman_settings as settings
from tests import EXTERNAL_DB_NAME, READ_ONLY_USER


def clear_directory(directory):
    if os.path.exists(directory):
        for the_file in os.listdir(directory):
            file_path = os.path.join(directory, the_file)
            print(f"Removing filesystem path {file_path}")
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)


def main():
    print(f"Clearing Layman data.")
    # filesystem
    clear_directory(settings.LAYMAN_DATA_DIR)

    # qgis
    clear_directory(settings.LAYMAN_QGIS_DATA_DIR)

    # normalized raster data
    clear_directory(settings.LAYMAN_NORMALIZED_RASTER_DATA_DIR)

    # postgresql
    import psycopg2
    conn_dict = settings.PG_CONN.copy()
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
    print(f"Dropping schemas in DB {conn_dict['dbname']}: {[r[1] for r in rows]}")
    for row in rows:
        cur.execute(f"""DROP SCHEMA "{row[1]}" CASCADE""")
    print(f"Dropping external test DB '{EXTERNAL_DB_NAME}'")
    cur.execute(f"""
DROP DATABASE IF EXISTS {EXTERNAL_DB_NAME} WITH (FORCE)
    """)
    print(f"Dropping user '{READ_ONLY_USER}'")
    cur.execute(f"""
DROP USER IF EXISTS {READ_ONLY_USER}
    """)
    conn.close()

    # redis
    print(f"Flushing Redis DB {settings.LAYMAN_REDIS_URL}")
    settings.LAYMAN_REDIS.flushdb()
    print(f"Flushing Redis DB {os.environ['LTC_REDIS_URI']}")
    settings.LAYMAN_LTC_REDIS.flushdb()

    # geoserver
    import requests
    headers_json = {
        'Accept': 'application/json',
        'Content-type': 'application/json',
    }

    auth = settings.GEOSERVER_ADMIN_AUTH or settings.LAYMAN_GS_AUTH
    response = requests.get(geoserver.GS_REST_USERS,
                            headers=headers_json,
                            auth=auth,
                            timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
                            )
    response.raise_for_status()
    all_users = [u['userName'] for u in response.json()['users']]
    if settings.LAYMAN_GS_USER in all_users:
        all_users.remove(settings.LAYMAN_GS_USER)

    for user in all_users:
        response = requests.get(urljoin(geoserver.GS_REST_ROLES, f'user/{user}/'),
                                headers=headers_json,
                                auth=auth,
                                timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
                                )
        response.raise_for_status()
        roles = response.json()['roles']

        if settings.LAYMAN_GS_ROLE in roles:
            response = requests.delete(
                urljoin(geoserver.GS_REST_SECURITY_ACL_LAYERS, user + '.*.r'),
                headers=headers_json,
                auth=auth,
                timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
            )
            if response.status_code != 404:
                response.raise_for_status()

            response = requests.delete(
                urljoin(geoserver.GS_REST_SECURITY_ACL_LAYERS, user + '.*.w'),
                headers=headers_json,
                auth=auth,
                timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
            )
            if response.status_code != 404:
                response.raise_for_status()

            response = requests.delete(
                urljoin(geoserver.GS_REST_WORKSPACES, user),
                headers=headers_json,
                auth=auth,
                params={
                    'recurse': 'true'
                },
                timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
            )
            response.raise_for_status()

            for role in roles:
                response = requests.delete(
                    urljoin(geoserver.GS_REST_ROLES, f'role/{role}/user/{user}/'),
                    headers=headers_json,
                    auth=auth,
                    timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
                )
                response.raise_for_status()

            response = requests.delete(
                urljoin(geoserver.GS_REST_ROLES, 'role/' + f"USER_{user.upper()}"),
                headers=headers_json,
                auth=auth,
                timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
            )
            if response.status_code != 404:
                response.raise_for_status()

            response = requests.delete(
                urljoin(geoserver.GS_REST_USER, user),
                headers=headers_json,
                auth=auth,
                timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
            )
            response.raise_for_status()

    response = requests.get(geoserver.GS_REST_WORKSPACES,
                            headers=headers_json,
                            auth=auth,
                            timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
                            )
    response.raise_for_status()

    if response.json()['workspaces'] != "":
        all_workspaces = [workspace["name"] for workspace in response.json()['workspaces']['workspace']]
        for workspace in all_workspaces:
            response = requests.delete(
                urljoin(geoserver.GS_REST_WORKSPACES, workspace),
                headers=headers_json,
                auth=auth,
                params={
                    'recurse': 'true'
                },
                timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
            )
            response.raise_for_status()

    # micka
    record_ids_to_delete = micka.csw_get_record_ids_containing_url(settings.CSW_URL, auth=settings.CSW_BASIC_AUTHN, contained_url_part=f"://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/")

    opts = {} if settings.CSW_BASIC_AUTHN is None else {
        'username': settings.CSW_BASIC_AUTHN[0],
        'password': settings.CSW_BASIC_AUTHN[1],
    }
    opts['skip_caps'] = True
    from owslib.csw import CatalogueServiceWeb
    csw = CatalogueServiceWeb(settings.CSW_URL, **opts) if settings.CSW_URL is not None else None
    assert csw.exceptionreport is None
    for record_id in record_ids_to_delete:
        print(f"Deleting metadata record {record_id}")
        csw.transaction(ttype='delete', typename='gmd:MD_Metadata', identifier=record_id)

    # Layman DB
    conn = psycopg2.connect(**settings.PG_CONN)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"""
DROP SCHEMA IF EXISTS "{settings.LAYMAN_PRIME_SCHEMA}" CASCADE;
""")
    conn.commit()


if __name__ == "__main__":
    main()
