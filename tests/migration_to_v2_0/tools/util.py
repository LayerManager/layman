import time

import requests
from requests.exceptions import ConnectionError


def wait_for_url(url, max_attempts, sleeping_time):
    attempt = 1
    while True:
        # print(f"Waiting for URL {url}, attempt {attempt}")
        try:
            # Just checking the url, no need to store result
            requests.get(url, timeout=1)
            break
        except ConnectionError as exception:
            if attempt == max_attempts:
                print(f"Max attempts reached")
                raise exception
            attempt += 1
        time.sleep(sleeping_time)
