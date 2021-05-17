import importlib
import os
import shutil
from urllib.parse import urljoin

import geoserver

settings = importlib.import_module(os.environ['LAYMAN_SETTINGS_MODULE'])


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
    conn.close()

    # redis
    print(f"Flushing Redis DB {settings.LAYMAN_REDIS_URL}")
    settings.LAYMAN_REDIS.flushdb()
    import redis
    print(f"Flushing Redis DB {os.environ['LTC_REDIS_URI']}")
    ltc_redis = redis.Redis.from_url(os.environ['LTC_REDIS_URI'], encoding="utf-8", decode_responses=True)
    ltc_redis.flushdb()

    # geoserver
    import requests
    headers_json = {
        'Accept': 'application/json',
        'Content-type': 'application/json',
    }

    auth = settings.GEOSERVER_ADMIN_AUTH or settings.LAYMAN_GS_AUTH
    response = requests.get(geoserver.GS_REST_USERS,
                            headers=headers_json,
                            auth=auth
                            )
    response.raise_for_status()
    all_users = [u['userName'] for u in response.json()['users']]
    if settings.LAYMAN_GS_USER in all_users:
        all_users.remove(settings.LAYMAN_GS_USER)

    for user in all_users:
        response = requests.get(urljoin(geoserver.GS_REST_ROLES, f'user/{user}/'),
                                headers=headers_json,
                                auth=auth
                                )
        response.raise_for_status()
        roles = response.json()['roleNames']

        if settings.LAYMAN_GS_ROLE in roles:
            response = requests.delete(
                urljoin(geoserver.GS_REST_SECURITY_ACL_LAYERS, user + '.*.r'),
                headers=headers_json,
                auth=auth
            )
            if response.status_code != 404:
                response.raise_for_status()

            response = requests.delete(
                urljoin(geoserver.GS_REST_SECURITY_ACL_LAYERS, user + '.*.w'),
                headers=headers_json,
                auth=auth
            )
            if response.status_code != 404:
                response.raise_for_status()

            response = requests.delete(
                urljoin(geoserver.GS_REST_WORKSPACES, user),
                headers=headers_json,
                auth=auth,
                params={
                    'recurse': 'true'
                }
            )
            response.raise_for_status()

            for role in roles:
                response = requests.delete(
                    urljoin(geoserver.GS_REST_ROLES, f'role/{role}/user/{user}/'),
                    headers=headers_json,
                    auth=auth,
                )
                response.raise_for_status()

            response = requests.delete(
                urljoin(geoserver.GS_REST_ROLES, 'role/' + f"USER_{user.upper()}"),
                headers=headers_json,
                auth=auth,
            )
            if response.status_code != 404:
                response.raise_for_status()

            response = requests.delete(
                urljoin(geoserver.GS_REST_USER, user),
                headers=headers_json,
                auth=auth,
            )
            response.raise_for_status()

    response = requests.get(geoserver.GS_REST_WORKSPACES,
                            headers=headers_json,
                            auth=auth
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
                }
            )
            response.raise_for_status()

    # micka
    opts = {} if settings.CSW_BASIC_AUTHN is None else {
        'username': settings.CSW_BASIC_AUTHN[0],
        'password': settings.CSW_BASIC_AUTHN[1],
    }
    opts['skip_caps'] = True
    from owslib.csw import CatalogueServiceWeb
    csw = CatalogueServiceWeb(settings.CSW_URL, **opts) if settings.CSW_URL is not None else None
    csw.getrecords2(xml=f"""
        <csw:GetRecords xmlns:ogc="http://www.opengis.net/ogc" xmlns:csw="http://www.opengis.net/cat/csw/2.0.2" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dct="http://purl.org/dc/terms/" xmlns:ows="http://www.opengis.net/ows" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:apiso="http://www.opengis.net/cat/csw/apiso/1.0" xmlns:gmd="http://www.isotc211.org/2005/gmd" outputSchema="http://www.isotc211.org/2005/gmd" maxRecords="100" startPosition="1" outputFormat="application/xml" service="CSW" resultType="results" version="2.0.2" requestId="1" debug="0">
         <csw:Query typeNames="gmd:MD_Metadata">
          <csw:ElementSetName>summary</csw:ElementSetName>
          <csw:Constraint version="1.1.0">
           <ogc:Filter xmlns:gml="http://www.opengis.net/gml">
             <ogc:PropertyIsLike wildCard="*" singleChar="@" escapeChar="\\">
               <ogc:PropertyName>apiso:Identifier</ogc:PropertyName>
               <ogc:Literal>*</ogc:Literal>
             </ogc:PropertyIsLike>
           </ogc:Filter>
          </csw:Constraint>
         </csw:Query>
        </csw:GetRecords>
        """)
    assert csw.exceptionreport is None
    items = csw.records.items()
    for record_id, record in items:
        urls = [ol.url for ol in record.distribution.online]
        url_part = f"://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/"
        if any((url_part in u for u in urls)):
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
