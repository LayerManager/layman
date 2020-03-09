import importlib
import os
import re
import sys
import time
import traceback
from urllib.parse import urlparse


settings = importlib.import_module(os.environ['LAYMAN_SETTINGS_MODULE'])

ATTEMPT_INTERVAL = 2
MAX_ATTEMPTS = 60

MICKA_VERSION_RE = r":\s*([^:()\s]+)\s*\(\s*rev\.\s*([^:()\s]+)\s*\)"


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
        except redis.exceptions.ConnectionError as e:
            handle_exception(e, attempt, wait_for_msg)
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
            with psycopg2.connect(**conn_dict) as conn:
                pass
            print(f"Attempt {attempt}/{MAX_ATTEMPTS} successful.")
            break
        except psycopg2.OperationalError as e:
            handle_exception(e, attempt, wait_for_msg)
            attempt += 1
    print()

    # GeoServer
    headers_json = {
        'Accept': 'application/json',
        'Content-type': 'application/json',
    }
    wait_for_msg = f"GeoServer REST API, user={settings.LAYMAN_GS_USER}, url={settings.LAYMAN_GS_REST_WORKSPACES}"
    print(f"Waiting for {wait_for_msg}")
    while True:
        import requests
        try:
            r = requests.get(
                settings.LAYMAN_GS_REST_WORKSPACES,
                headers=headers_json,
                auth=settings.LAYMAN_GS_AUTH,
                timeout=0.1
            )
            r.raise_for_status()
            print(f"Attempt {attempt}/{MAX_ATTEMPTS} successful.")
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
            handle_exception(e, attempt, wait_for_msg)
            attempt += 1
    print()

    # Layman Test Client
    ltc_url = f"{settings.LAYMAN_CLIENT_URL}static/test-client/global.css"
    wait_for_msg = f"Layman Test Client, url={ltc_url}"
    print(f"Waiting for {wait_for_msg}")
    while True:
        try:
            r = requests.get(
                ltc_url,
                allow_redirects=False,
                timeout=0.1
            )
            r.raise_for_status()
            print(f"Attempt {attempt}/{MAX_ATTEMPTS} successful.")
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
            handle_exception(e, attempt, wait_for_msg)
            attempt += 1
    print()


    # Micka
    micka_url = urlparse(settings.CSW_URL)._replace(path="/about").geturl()
    wait_for_msg = f"Micka, url={micka_url}"
    print(f"Waiting for {wait_for_msg}")
    while True:
        try:
            r = requests.get(
                micka_url,
                allow_redirects=False,
                timeout=0.1
            )
            r.raise_for_status()
            response = r.text
            version_match = re.search(MICKA_VERSION_RE, response)
            assert (version_match and len(version_match.groups()) == 2), 'Unknown version of Micka!'
            found_version = version_match.groups()
            assert found_version in settings.MICKA_ACCEPTED_VERSIONS, f"Found Micka version {found_version}, but expecting one of {settings.MICKA_ACCEPTED_VERSIONS}. Please use one of expected version, e.g. by upgrading/downgrading Micka. Take special care about Micka's database."
            print(f"Found Micka version {found_version}.")

            print(f"Attempt {attempt}/{MAX_ATTEMPTS} successful.")
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
            handle_exception(e, attempt, wait_for_msg)
            attempt += 1
    print()


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
