import re
import sys
import time
from urllib.parse import urljoin

import geoserver
from geoserver.role_service import check_jdbc_role_service
import layman_settings as settings
from layman_start_util import validate_role_service

ATTEMPT_INTERVAL = 2
MAX_ATTEMPTS = 60

MICKA_VERSION_RE = r"\s*([^:()\s]+)\s*\(\s*rev\.\s*([^:()\s]+)\s*\)"


def main():
    attempt = 1

    # Redis
    import redis
    rds = redis.Redis.from_url(settings.LAYMAN_REDIS_URL, encoding="utf-8", decode_responses=True)
    wait_for_msg = f"Redis, url={settings.LAYMAN_REDIS_URL}"
    print(f"Waiting for {wait_for_msg}")
    while True:
        try:
            rds.ping()
            print(f"Attempt {attempt}/{MAX_ATTEMPTS} successful.")
            break
        except redis.exceptions.ConnectionError as exc:
            handle_exception(exc, attempt, wait_for_msg)
            attempt += 1
    print()

    # PostgreSQL
    conn_dict = settings.PG_CONN.copy()
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
        except psycopg2.OperationalError as exc:
            handle_exception(exc, attempt, wait_for_msg)
            attempt += 1
    print()

    # Check PostgreSQL role service and stops immediately in case of any error
    print(f"Checking PostgreSQL role service")
    check_jdbc_role_service(settings.LAYMAN_ROLE_SERVICE_URI, settings.LAYMAN_ROLE_SERVICE_SCHEMA)
    validate_role_service(layman_usernames=[])
    print()

    # QGIS Server
    wait_for_msg = f"QGIS Server, url={settings.LAYMAN_QGIS_URL}"
    print(f"Waiting for {wait_for_msg}")
    while True:
        import requests
        try:
            response = requests.get(
                settings.LAYMAN_QGIS_URL,
                timeout=1
            )
            expected_text = "<ServerException>Project file error. For OWS services: please provide a SERVICE and a MAP parameter pointing to a valid QGIS project file</ServerException>"
            if response.status_code == 500 and expected_text in response.text:
                print(f"Attempt {attempt}/{MAX_ATTEMPTS} successful.")
                break
            response.raise_for_status()
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout, requests.exceptions.HTTPError) as exc:
            handle_exception(exc, attempt, wait_for_msg)
            attempt += 1
    print()

    # GeoServer
    headers_json = {
        'Accept': 'application/json',
        'Content-type': 'application/json',
    }
    auth = settings.GEOSERVER_ADMIN_AUTH or settings.LAYMAN_GS_AUTH
    wait_for_msg = f"GeoServer REST API, user={auth[0]}, url={geoserver.GS_REST_WORKSPACES}"
    print(f"Waiting for {wait_for_msg}")
    while True:
        import requests
        try:
            response = requests.get(
                geoserver.GS_REST_WORKSPACES,
                headers=headers_json,
                auth=auth,
                timeout=0.1
            )
            response.raise_for_status()
            print(f"Attempt {attempt}/{MAX_ATTEMPTS} successful.")
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as exc:
            handle_exception(exc, attempt, wait_for_msg)
            attempt += 1
    print()

    # Layman Test Client
    ltc_url = f"{settings.LAYMAN_CLIENT_URL}static/global.css"
    wait_for_msg = f"Layman Test Client, url={ltc_url}"
    print(f"Waiting for {wait_for_msg}")
    while True:
        try:
            response = requests.get(
                ltc_url,
                allow_redirects=False,
                timeout=0.1
            )
            response.raise_for_status()
            print(f"Attempt {attempt}/{MAX_ATTEMPTS} successful.")
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as exc:
            handle_exception(exc, attempt, wait_for_msg)
            attempt += 1
    print()

    # Micka
    micka_url = urljoin(settings.CSW_URL, "about")
    wait_for_msg = f"Micka, url={micka_url}"
    print(f"Waiting for {wait_for_msg}")
    while True:
        try:
            response = requests.get(
                micka_url,
                allow_redirects=False,
                timeout=0.1
            )
            response.raise_for_status()
            response = response.text
            version_match = re.search(MICKA_VERSION_RE, response)
            assert (version_match and len(version_match.groups()) == 2), 'Unknown version of Micka!'
            found_version = version_match.groups()
            err_message = f"Found Micka version {found_version}, but expecting version fulfilling {settings.MICKA_ACCEPTED_VERSION}. Please use one of expected version, e.g. by upgrading/downgrading Micka. Take special care about Micka's database."
            if settings.MICKA_ACCEPTED_VERSION[0] == '>=':
                assert found_version[0] >= settings.MICKA_ACCEPTED_VERSION[1] and found_version[1] >= settings.MICKA_ACCEPTED_VERSION[2], err_message
            elif settings.MICKA_ACCEPTED_VERSION[0] in ('==', ''):
                assert found_version == settings.MICKA_ACCEPTED_VERSION[1:], err_message
            else:
                raise NotImplementedError(f"Unknown Micka version comparision: {settings.MICKA_ACCEPTED_VERSION[0]}")
            print(f"Found Micka version {found_version}.")

            print(f"Attempt {attempt}/{MAX_ATTEMPTS} successful.")
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as exc:
            handle_exception(exc, attempt, wait_for_msg)
            attempt += 1
    print()


def handle_exception(_e, attempt, wait_for_msg=None):
    # traceback.print_exc()
    if attempt >= MAX_ATTEMPTS:
        print(f"Reaching max attempts when waiting for {wait_for_msg}")
        sys.exit(1)
        # raise e
    time.sleep(ATTEMPT_INTERVAL)


if __name__ == "__main__":
    main()
