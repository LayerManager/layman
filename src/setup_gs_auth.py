import importlib
import logging
import os
import requests
import sys
import time
import traceback
from geoserver import authn as gs_authn

settings = importlib.import_module(os.environ['LAYMAN_SETTINGS_MODULE'])


logger = logging.getLogger(__name__)

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

ATTEMPT_INTERVAL = 2
MAX_ATTEMPTS = 60


def main():
    attempt = 1

    # Wait for GeoServer
    headers_json = {
        'Accept': 'application/json',
        'Content-type': 'application/json',
    }
    auth = settings.GEOSERVER_ADMIN_AUTH or settings.LAYMAN_GS_AUTH
    wait_for_msg = f"GeoServer REST API, user={auth[0]}, url={settings.LAYMAN_GS_REST_WORKSPACES}"
    print(f"Waiting for {wait_for_msg}")
    while True:
        try:
            r = requests.get(
                settings.LAYMAN_GS_REST_WORKSPACES,
                headers=headers_json,
                auth=auth,
                timeout=0.1
            )
            r.raise_for_status()
            print(f"Attempt {attempt}/{MAX_ATTEMPTS} successful.")
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
            handle_exception(e, attempt, wait_for_msg)
            attempt += 1
    print(f"settings.GEOSERVER_DATADIR={settings.GEOSERVER_DATADIR}")

    assert os.path.exists(settings.GEOSERVER_DATADIR)

    gs_authn.ensure_request_header_authn(
        settings.GEOSERVER_DATADIR,
        settings.LAYMAN_GS_AUTHN_HTTP_HEADER_NAME,
        settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE,
        settings.LAYMAN_GS_USER_GROUP_SERVICE,
        settings.LAYMAN_GS_ROLE_SERVICE
    )
    # TODO ensure the filter to be inserted before 'default' filter group
    gs_authn.ensure_security_filter_group(
        settings.GEOSERVER_DATADIR,
        settings.LAYMAN_GS_AUTHN_FILTER_NAME,
        [
            settings.LAYMAN_GS_AUTHN_HTTP_HEADER_NAME,
            'basic',
            'anonymous',
        ]
    )

    # TODO does not refresh new filter group (only after restart)
    logger.info(f"Resetting GeoServer configuration ...")
    r = requests.post(
        settings.LAYMAN_GS_REST+'reset',
        headers=headers_json,
        auth=auth,
        timeout=0.1
    )
    r.raise_for_status()
    logger.info(f"Resetting GeoServer configuration finished.")

    # TODO raises Error for some reason
    # logger.info(f"Reloading GeoServer configuration ...")
    # r = requests.post(
    #     settings.LAYMAN_GS_REST+'reload',
    #     headers=headers_json,
    #     auth=auth,
    #     timeout=0.1
    # )
    # r.raise_for_status()
    # logger.info(f"Reloading GeoServer configuration finished.")


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
        logger.warning(f"Reaching max attempts when waiting for {wait_for_msg}")
        sys.exit(1)
        # raise e
    time.sleep(ATTEMPT_INTERVAL)


if __name__ == "__main__":
    main()
