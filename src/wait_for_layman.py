import sys
import time

import layman_settings as settings

ATTEMPT_INTERVAL = 2
MAX_ATTEMPTS = 100


def main():
    attempt = 1

    # Layman Server
    url = f"http://{settings.LAYMAN_SERVER_NAME}/rest/about/version"
    wait_for_msg = f"Layman Server, url={url}"
    print(f"Waiting for {wait_for_msg}")
    while True:
        import requests
        try:
            response = requests.get(
                url,
                timeout=0.1
            )
            response.raise_for_status()
            print(f"Attempt {attempt}/{MAX_ATTEMPTS} successful.")
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout, requests.exceptions.HTTPError) as exc:
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
